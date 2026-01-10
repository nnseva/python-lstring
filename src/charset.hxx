#ifndef LSTRING_CHARSET_HXX
#define LSTRING_CHARSET_HXX

#include <Python.h>
#include <algorithm>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <vector>

class CharSet {
public:
    CharSet() = default;
    virtual ~CharSet() = default;

    virtual const bool is_in(Py_UCS4 ch) const = 0;
};

class ByteCharSet final : public CharSet {
public:
    ByteCharSet(const Py_UCS1* charset, Py_ssize_t length) : mask_{0, 0, 0, 0} {
        if (!charset && length != 0) {
            throw std::invalid_argument("ByteCharSet: charset is null");
        }
        for (Py_ssize_t i = 0; i < length; ++i) {
            const uint32_t ch = static_cast<uint32_t>(charset[i]);
            mask_[ch >> 6] |= (1ULL << (ch & 63));
        }
    }

    const bool is_in(Py_UCS4 ch) const override {
        if (ch > 0xFF) {
            return false;
        }
        const uint32_t u = static_cast<uint32_t>(ch);
        return (mask_[u >> 6] & (1ULL << (u & 63))) != 0;
    }

private:
    uint64_t mask_[4];
};

class SingleCharSet final : public CharSet {
public:
    SingleCharSet(const Py_UCS2* charset, Py_ssize_t length, Py_UCS4 min_char, Py_UCS4 max_char)
        : min_char_(min_char), max_char_(max_char), mask_{0, 0, 0, 0} {
        init_and_fill(charset, length);
    }

    SingleCharSet(const Py_UCS4* charset, Py_ssize_t length, Py_UCS4 min_char, Py_UCS4 max_char)
        : min_char_(min_char), max_char_(max_char), mask_{0, 0, 0, 0} {
        init_and_fill(charset, length);
    }

    const bool is_in(Py_UCS4 ch) const override {
        if (ch < min_char_ || ch >= max_char_) {
            return false;
        }
        const uint32_t idx = static_cast<uint32_t>(ch - min_char_);
        return (mask_[idx >> 6] & (1ULL << (idx & 63))) != 0;
    }

private:
    template <class T>
    void init_and_fill(const T* charset, Py_ssize_t length) {
        if (!charset && length != 0) {
            throw std::invalid_argument("SingleCharSet: charset is null");
        }
        if (max_char_ <= min_char_) {
            throw std::invalid_argument("SingleCharSet: max_char must be greater than min_char");
        }
        const Py_UCS4 span = max_char_ - min_char_;
        if (span > 256) {
            throw std::invalid_argument("SingleCharSet: range too wide for 256-bit mask");
        }

        for (Py_ssize_t i = 0; i < length; ++i) {
            const Py_UCS4 ch = static_cast<Py_UCS4>(charset[i]);
            if (ch < min_char_ || ch >= max_char_) {
                throw std::invalid_argument("SingleCharSet: charset element out of [min_char, max_char) range");
            }
            const uint32_t idx = static_cast<uint32_t>(ch - min_char_);
            mask_[idx >> 6] |= (1ULL << (idx & 63));
        }
    }

    Py_UCS4 min_char_;
    Py_UCS4 max_char_;
    uint64_t mask_[4];
};

class FullCharSet final : public CharSet {
public:
    FullCharSet() = default;

    FullCharSet(const Py_UCS1* charset, Py_ssize_t length) {
        if (!charset && length != 0) {
            throw std::invalid_argument("FullCharSet: charset is null");
        }
        if (length > 0) {
            sets_.push_back(std::make_unique<ByteCharSet>(charset, length));
        }
    }

    FullCharSet(const Py_UCS2* charset, Py_ssize_t length) {
        build_from_unicode_array(charset, length);
    }

    FullCharSet(const Py_UCS4* charset, Py_ssize_t length) {
        build_from_unicode_array(charset, length);
    }

    const bool is_in(Py_UCS4 ch) const override {
        for (const auto& set : sets_) {
            if (set->is_in(ch)) {
                return true;
            }
        }
        return false;
    }

private:
    template <class T>
    void build_from_unicode_array(const T* charset, Py_ssize_t length) {
        if (!charset && length != 0) {
            throw std::invalid_argument("FullCharSet: charset is null");
        }
        if (length <= 0) {
            return;
        }

        std::vector<Py_UCS1> byte_chars;
        std::vector<Py_UCS4> high_chars;
        byte_chars.reserve(static_cast<size_t>(length));
        high_chars.reserve(static_cast<size_t>(length));

        for (Py_ssize_t i = 0; i < length; ++i) {
            const Py_UCS4 ch = static_cast<Py_UCS4>(charset[i]);
            if (ch <= 0xFF) {
                byte_chars.push_back(static_cast<Py_UCS1>(ch));
            } else {
                high_chars.push_back(ch);
            }
        }

        if (!byte_chars.empty()) {
            sets_.push_back(std::make_unique<ByteCharSet>(byte_chars.data(), static_cast<Py_ssize_t>(byte_chars.size())));
        }

        if (high_chars.empty()) {
            return;
        }

        std::sort(high_chars.begin(), high_chars.end());
        high_chars.erase(std::unique(high_chars.begin(), high_chars.end()), high_chars.end());

        // Greedy heuristic: start a new range when span would exceed 256.
        // This isn't necessarily globally optimal, but is fast and usually compact.
        size_t start = 0;
        while (start < high_chars.size()) {
            const Py_UCS4 min_char = high_chars[start];
            size_t end = start + 1;
            while (end < high_chars.size() && (high_chars[end] - min_char) <= 255) {
                ++end;
            }
            const Py_UCS4 max_char = high_chars[end - 1] + 1;
            const Py_ssize_t chunk_len = static_cast<Py_ssize_t>(end - start);
            sets_.push_back(std::make_unique<SingleCharSet>(high_chars.data() + start, chunk_len, min_char, max_char));
            start = end;
        }
    }

    std::vector<std::unique_ptr<CharSet>> sets_;
};

#endif // LSTRING_CHARSET_HXX
