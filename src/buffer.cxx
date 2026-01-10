#include "lstring/lstring.hxx"
#include "_lstring.hxx"
#include "charset.hxx"

Buffer* Buffer::optimize() {
    if (LStr_optimize_threshold <= 0) return nullptr;
    if ((Py_ssize_t)length() < LStr_optimize_threshold)
        return collapse();
    return nullptr;
}

Buffer::~Buffer() {}

bool Buffer::is_str() const {
    return false;
}

Py_ssize_t Buffer::findcs(Py_ssize_t start, Py_ssize_t end, const CharSet& charset, bool invert) const {
    if (start < 0) start = 0;
    Py_ssize_t len = length();
    if (end > len) end = len;
    if (start >= end) return -1;
    for (Py_ssize_t i = start; i < end; ++i) {
        uint32_t ch = value(i);
        bool found = charset.is_in(ch);
        if (found != invert) {
            return i;
        }
    }
    return -1;
}

Py_ssize_t Buffer::rfindcs(Py_ssize_t start, Py_ssize_t end, const CharSet& charset, bool invert) const {
    if (start < 0) start = 0;
    Py_ssize_t len = length();
    if (end > len) end = len;
    if (start >= end) return -1;
    for (Py_ssize_t i = end - 1; i >= start; --i) {
        uint32_t ch = value(i);
        bool found = charset.is_in(ch);
        if (found != invert) {
            return i;
        }
    }
    return -1;
}

Py_ssize_t Buffer::findcr(Py_ssize_t start, Py_ssize_t end, uint32_t startcp, uint32_t endcp, bool invert) const {
    if (start < 0) start = 0;
    Py_ssize_t len = length();
    if (end > len) end = len;
    if (start >= end) return -1;
    if (startcp >= endcp) return -1;

    for (Py_ssize_t i = start; i < end; ++i) {
        uint32_t ch = value(i);
        bool in_range = (ch >= startcp && ch < endcp);
        if (in_range != invert) {
            return i;
        }
    }
    return -1;
}

Py_ssize_t Buffer::rfindcr(Py_ssize_t start, Py_ssize_t end, uint32_t startcp, uint32_t endcp, bool invert) const {
    if (start < 0) start = 0;
    Py_ssize_t len = length();
    if (end > len) end = len;
    if (start >= end) return -1;
    if (startcp >= endcp) return -1;

    for (Py_ssize_t i = end - 1; i >= start; --i) {
        uint32_t ch = value(i);
        bool in_range = (ch >= startcp && ch < endcp);
        if (in_range != invert) {
            return i;
        }
    }
    return -1;
}

Py_ssize_t Buffer::findcc(Py_ssize_t start, Py_ssize_t end, uint32_t class_mask, bool invert) const {
    if (start < 0) start = 0;
    Py_ssize_t len = length();
    if (end > len) end = len;
    if (start >= end) return -1;

    for (Py_ssize_t i = start; i < end; ++i) {
        bool matches = char_is(value(i), class_mask);
        if (matches != invert) {
            return i;
        }
    }
    return -1;
}

Py_ssize_t Buffer::rfindcc(Py_ssize_t start, Py_ssize_t end, uint32_t class_mask, bool invert) const {
    if (start < 0) start = 0;
    Py_ssize_t len = length();
    if (end > len) end = len;
    if (start >= end) return -1;

    for (Py_ssize_t i = end - 1; i >= start; --i) {
        bool matches = char_is(value(i), class_mask);
        if (matches != invert) {
            return i;
        }
    }
    return -1;
}

int Buffer::cmp(const Buffer* other) const {
    Py_ssize_t len1 = length();
    Py_ssize_t len2 = other->length();
    Py_ssize_t minlen = (len1 < len2) ? len1 : len2;

    for (Py_ssize_t i = 0; i < minlen; ++i) {
        uint32_t c1 = value(i);
        uint32_t c2 = other->value(i);
        if (c1 < c2) return -1;
        if (c1 > c2) return 1;
    }
    if (len1 < len2) return -1;
    if (len1 > len2) return 1;
    return 0;
}

bool Buffer::isspace() const {
    Py_ssize_t len = length();
    if (len == 0) return false;
    for (Py_ssize_t i = 0; i < len; ++i) {
        if (!Py_UNICODE_ISSPACE(value(i))) {
            return false;
        }
    }
    return true;
}

bool Buffer::isalpha() const {
    Py_ssize_t len = length();
    if (len == 0) return false;
    for (Py_ssize_t i = 0; i < len; ++i) {
        if (!Py_UNICODE_ISALPHA(value(i))) {
            return false;
        }
    }
    return true;
}

bool Buffer::isdigit() const {
    Py_ssize_t len = length();
    if (len == 0) return false;
    for (Py_ssize_t i = 0; i < len; ++i) {
        if (!Py_UNICODE_ISDIGIT(value(i))) {
            return false;
        }
    }
    return true;
}

bool Buffer::isalnum() const {
    Py_ssize_t len = length();
    if (len == 0) return false;
    for (Py_ssize_t i = 0; i < len; ++i) {
        if (!Py_UNICODE_ISALNUM(value(i))) {
            return false;
        }
    }
    return true;
}

bool Buffer::isupper() const {
    Py_ssize_t len = length();
    if (len == 0) return false;
    bool has_cased = false;
    for (Py_ssize_t i = 0; i < len; ++i) {
        Py_UCS4 ch = value(i);
        if (Py_UNICODE_ISLOWER(ch)) {
            return false;
        }
        if (Py_UNICODE_ISUPPER(ch)) {
            has_cased = true;
        }
    }
    return has_cased;
}

bool Buffer::islower() const {
    Py_ssize_t len = length();
    if (len == 0) return false;
    bool has_cased = false;
    for (Py_ssize_t i = 0; i < len; ++i) {
        Py_UCS4 ch = value(i);
        if (Py_UNICODE_ISUPPER(ch)) {
            return false;
        }
        if (Py_UNICODE_ISLOWER(ch)) {
            has_cased = true;
        }
    }
    return has_cased;
}

bool Buffer::isdecimal() const {
    Py_ssize_t len = length();
    if (len == 0) return false;
    for (Py_ssize_t i = 0; i < len; ++i) {
        if (!Py_UNICODE_ISDECIMAL(value(i))) {
            return false;
        }
    }
    return true;
}

bool Buffer::isnumeric() const {
    Py_ssize_t len = length();
    if (len == 0) return false;
    for (Py_ssize_t i = 0; i < len; ++i) {
        if (!Py_UNICODE_ISNUMERIC(value(i))) {
            return false;
        }
    }
    return true;
}

bool Buffer::isprintable() const {
    Py_ssize_t len = length();
    if (len == 0) return true;
    for (Py_ssize_t i = 0; i < len; ++i) {
        if (!Py_UNICODE_ISPRINTABLE(value(i))) {
            return false;
        }
    }
    return true;
}

bool Buffer::istitle() const {
    return check_istitle_range(length());
}

Buffer* Buffer::collapse() {
    return nullptr;
}
