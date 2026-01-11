#ifndef LSTRING_CHARSET_HXX
#define LSTRING_CHARSET_HXX

#include <Python.h>
#include <algorithm>
#include <cstdint>
#include <memory>
#include <stdexcept>
#include <vector>

#include "lstring/lstring.hxx"

class CharSet {
public:
    CharSet() = default;
    virtual ~CharSet() = default;

    virtual const bool is_in(Py_UCS4 ch) const = 0;
    virtual Py_UCS4 min_char() const = 0;
    virtual Py_UCS4 max_char() const = 0;
};

class ByteCharSet final : public CharSet {
public:
    ByteCharSet(const Py_UCS1* charset, Py_ssize_t length) : mask_{0, 0, 0, 0} {
        init_and_fill(charset, length);
    }

    ByteCharSet(const Py_UCS2* charset, Py_ssize_t length) : mask_{0, 0, 0, 0} {
        init_and_fill(charset, length);
    }

    ByteCharSet(const Py_UCS4* charset, Py_ssize_t length) : mask_{0, 0, 0, 0} {
        init_and_fill(charset, length);
    }

    const bool is_in(Py_UCS4 ch) const override {
        if (ch > 0xFF) {
            return false;
        }
        const uint32_t u = static_cast<uint32_t>(ch);
        return (mask_[u >> 6] & (1ULL << (u & 63))) != 0;
    }

    Py_UCS4 min_char() const override {
        return 0;
    }
    Py_UCS4 max_char() const override {
        return 256;
    }
private:
    template <class T>
    void init_and_fill(const T* charset, Py_ssize_t length) {
        if (!charset && length != 0) {
            throw std::invalid_argument("ByteCharSet: charset is null");
        }
        for (Py_ssize_t i = 0; i < length; ++i) {
            const Py_UCS4 ch = static_cast<Py_UCS4>(charset[i]);
            if (ch > 0xFF) {
                throw std::invalid_argument("ByteCharSet: charset element out of [0, 256) range");
            }
            const uint32_t u = static_cast<uint32_t>(ch);
            mask_[u >> 6] |= (1ULL << (u & 63));
        }
    }

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

    Py_UCS4 min_char() const override {
        return min_char_;
    }
    Py_UCS4 max_char() const override {
        return max_char_;
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

    explicit FullCharSet(const Buffer& buf) {
        build_from_buffer(buf);
    }

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
        if (sets_.empty()) {
            return false;
        }

        // sets_ is built as a monotonically increasing list of non-intersecting
        // [min_char, max_char) ranges, so we can avoid scanning all sets.
        const Py_UCS4 first_min = min_char();
        if (ch < first_min) {
            return false;
        }
        const Py_UCS4 last_max = max_char();
        if (ch >= last_max) {
            return false;
        }

        // Find the first range with max_char() > ch.
        size_t lo = 0;
        size_t hi = sets_.size();
        while (lo < hi) {
            const size_t mid = lo + ((hi - lo) >> 1);
            if (ch < sets_[mid]->max_char()) {
                hi = mid;
            } else {
                lo = mid + 1;
            }
        }
        if (lo >= sets_.size()) {
            return false;
        }

        const CharSet* candidate = sets_[lo].get();
        if (ch < candidate->min_char()) {
            return false;
        }
        return candidate->is_in(ch);
    }

    Py_UCS4 min_char() const override {
        if (sets_.empty()) {
            return 0;
        }
        return sets_.front()->min_char();
    }
    Py_UCS4 max_char() const override {
        if (sets_.empty()) {
            return 0;
        }
        return sets_.back()->max_char();
    }
private:
    template <class GetChar>
    void build_from_indexed(Py_ssize_t length, GetChar get_char) {
        if (length <= 0) {
            return;
        }

        std::vector<Py_UCS4> chars;
        chars.reserve(static_cast<size_t>(length));

        for (Py_ssize_t i = 0; i < length; ++i) {
            const Py_UCS4 ch = static_cast<Py_UCS4>(get_char(i));
            chars.push_back(ch);
        }

        std::sort(chars.begin(), chars.end());

        const auto high_it = std::upper_bound(chars.begin(), chars.end(), static_cast<Py_UCS4>(0xFF));
        const Py_ssize_t byte_len = static_cast<Py_ssize_t>(high_it - chars.begin());
        if (byte_len > 0) {
            sets_.push_back(std::make_unique<ByteCharSet>(chars.data(), byte_len));
        }

        if (high_it == chars.end()) {
            return;
        }

        // Greedy heuristic: start a new range when span would exceed 256.
        // This isn't necessarily globally optimal, but is fast and usually compact.
        size_t start = static_cast<size_t>(high_it - chars.begin());
        while (start < chars.size()) {
            const Py_UCS4 min_char = chars[start];
            size_t end = start + 1;
            while (end < chars.size() && (chars[end] - min_char) <= 255) {
                ++end;
            }
            const Py_UCS4 max_char = chars[end - 1] + 1;
            const Py_ssize_t chunk_len = static_cast<Py_ssize_t>(end - start);
            sets_.push_back(
                std::make_unique<SingleCharSet>(chars.data() + start, chunk_len, min_char, max_char));
            start = end;
        }
    }

    void build_from_buffer(const Buffer& buf) {
        const Py_ssize_t length = buf.length();
        build_from_indexed(length, [&](Py_ssize_t i) { return buf.value(i); });
    }

    template <class T>
    void build_from_unicode_array(const T* charset, Py_ssize_t length) {
        if (!charset && length != 0) {
            throw std::invalid_argument("FullCharSet: charset is null");
        }

        build_from_indexed(length, [&](Py_ssize_t i) { return charset[i]; });
    }

    // Monotonically increasing min_char()/max_char() list of non-intersecting CharSet instances.
    std::vector<std::unique_ptr<CharSet>> sets_;
};

#endif // LSTRING_CHARSET_HXX
