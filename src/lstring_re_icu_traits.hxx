#ifndef LSTRING_RE_ICU_TRAITS_HXX
#define LSTRING_RE_ICU_TRAITS_HXX

#include <Python.h>

#include <cstddef>
#include <cstdint>
#include <vector>

#include <unicode/uchar.h>

namespace lstring_re {

// Minimal Boost.Regex traits implementation for 32-bit Unicode code points.
//
// Goals:
// - Avoid dependence on system locale and wchar_t width.
// - Provide Unicode-aware character classification and case folding via ICU
//   (common) APIs.
// - Keep collation support intentionally simple/Unicode-codepoint-based.
//
// This type is meant to be wrapped by boost::regex_traits_wrapper.
struct icu_u32_regex_traits {
    using char_type = Py_UCS4;
    using string_type = std::vector<char_type>;
    using locale_type = int;
    using char_class_type = std::uint64_t;

    icu_u32_regex_traits() = default;

    static std::size_t length(const char_type* p) {
        std::size_t result = 0;
        while (p && *p) {
            ++p;
            ++result;
        }
        return result;
    }

    char_type translate(char_type c) const { return c; }

    char_type translate_nocase(char_type c) const {
        // ICU expects UChar32.
        return static_cast<char_type>(::u_foldCase(static_cast<UChar32>(c), U_FOLD_CASE_DEFAULT));
    }

    template <class ForwardIterator>
    string_type transform(ForwardIterator p1, ForwardIterator p2) const {
        // Identity transform: codepoint order.
        return string_type(p1, p2);
    }

    template <class ForwardIterator>
    string_type transform_primary(ForwardIterator p1, ForwardIterator p2) const {
        // For our use-cases, primary transform == identity.
        return string_type(p1, p2);
    }

    template <class ForwardIterator>
    char_class_type lookup_classname(ForwardIterator p1, ForwardIterator p2) const {
        // Parse ASCII class names (POSIX / Perl classes) and map them to ICU-based masks.
        // We avoid locale-specific behavior here.
        char_class_type mask = 0;

        // Normalize to lowercase ASCII and strip whitespace, '-' and '_'.
        std::vector<char> name;
        for (auto it = p1; it != p2; ++it) {
            char_type c32 = static_cast<char_type>(*it);
            if (c32 > 0x7Fu) {
                // Non-ASCII -> not a builtin class name.
                return 0;
            }
            char c = static_cast<char>(c32);
            if (c == ' ' || c == '\t' || c == '-' || c == '_') {
                continue;
            }
            if (c >= 'A' && c <= 'Z') {
                c = static_cast<char>(c - 'A' + 'a');
            }
            name.push_back(c);
        }

        if (name.empty()) {
            return 0;
        }

        auto equals = [&](const char* s) -> bool {
            std::size_t n = 0;
            while (s[n]) ++n;
            if (n != name.size()) return false;
            for (std::size_t i = 0; i < n; ++i) {
                if (name[i] != s[i]) return false;
            }
            return true;
        };

        // Custom high bits (above ICU GC masks).
        constexpr char_class_type mask_blank = char_class_type(1) << 32;
        constexpr char_class_type mask_space = char_class_type(1) << 33;
        constexpr char_class_type mask_xdigit = char_class_type(1) << 34;
        constexpr char_class_type mask_underscore = char_class_type(1) << 35;
        constexpr char_class_type mask_unicode = char_class_type(1) << 36;

        // POSIX-ish / Perl-ish names.
        if (equals("alnum")) return static_cast<char_class_type>(U_GC_L_MASK | U_GC_ND_MASK);
        if (equals("alpha")) return static_cast<char_class_type>(U_GC_L_MASK);
        if (equals("blank")) return mask_blank;
        if (equals("cntrl")) return static_cast<char_class_type>(U_GC_CC_MASK | U_GC_CF_MASK | U_GC_ZL_MASK | U_GC_ZP_MASK);
        if (equals("digit") || equals("d")) return static_cast<char_class_type>(U_GC_ND_MASK);

        // graph/print are approximations based on general categories.
        // graph: anything printable excluding separators.
        if (equals("graph")) {
            constexpr char_class_type all_gc = 0xFFFFFFFFull;
            return all_gc & ~static_cast<char_class_type>(U_GC_CC_MASK | U_GC_CF_MASK | U_GC_CS_MASK | U_GC_CN_MASK | U_GC_Z_MASK);
        }
        if (equals("print")) {
            constexpr char_class_type all_gc = 0xFFFFFFFFull;
            // printable includes separators
            return all_gc & ~static_cast<char_class_type>(U_GC_CC_MASK | U_GC_CF_MASK | U_GC_CS_MASK | U_GC_CN_MASK);
        }

        if (equals("lower")) return static_cast<char_class_type>(U_GC_LL_MASK);
        if (equals("upper")) return static_cast<char_class_type>(U_GC_LU_MASK);
        if (equals("punct")) return static_cast<char_class_type>(U_GC_P_MASK);

        if (equals("space") || equals("s")) return static_cast<char_class_type>(U_GC_Z_MASK) | mask_space;

        if (equals("word") || equals("w")) {
            // Approximation close to Python's "word" definition:
            // letters + decimal digits + nonspacing marks + underscore.
            return static_cast<char_class_type>(U_GC_L_MASK | U_GC_ND_MASK | U_GC_MN_MASK) | mask_underscore;
        }

        if (equals("xdigit")) return static_cast<char_class_type>(U_GC_ND_MASK) | mask_xdigit;
        if (equals("unicode")) return mask_unicode;

        return mask;
    }

    template <class ForwardIterator>
    string_type lookup_collatename(ForwardIterator p1, ForwardIterator p2) const {
        // Collating elements are locale-dependent; we keep a simple identity mapping.
        return string_type(p1, p2);
    }

    bool isctype(char_type c, char_class_type mask) const {
        constexpr char_class_type mask_blank = char_class_type(1) << 32;
        constexpr char_class_type mask_space = char_class_type(1) << 33;
        constexpr char_class_type mask_xdigit = char_class_type(1) << 34;
        constexpr char_class_type mask_underscore = char_class_type(1) << 35;
        constexpr char_class_type mask_unicode = char_class_type(1) << 36;

        if (mask & mask_unicode) {
            // Any valid Unicode scalar value.
            if (c <= 0x10FFFFu) return true;
        }
        if ((mask & mask_underscore) && (c == static_cast<char_type>('_'))) {
            return true;
        }
        if (mask & mask_blank) {
            if (c == static_cast<char_type>(' ') || c == static_cast<char_type>('\t')) return true;
        }
        if (mask & mask_space) {
            // ICU White_Space property.
            if (::u_isUWhiteSpace(static_cast<UChar32>(c))) return true;
        }
        if (mask & mask_xdigit) {
            // Hex digits (ASCII).
            if ((c >= static_cast<char_type>('0') && c <= static_cast<char_type>('9')) ||
                (c >= static_cast<char_type>('a') && c <= static_cast<char_type>('f')) ||
                (c >= static_cast<char_type>('A') && c <= static_cast<char_type>('F'))) {
                return true;
            }
        }

        // Check ICU general category masks (lower 32 bits).
        const std::uint32_t gc_mask = U_GET_GC_MASK(static_cast<UChar32>(c));
        if (mask & static_cast<char_class_type>(gc_mask)) {
            return true;
        }
        return false;
    }

    int value(char_type c, int radix) const {
        // Numeric value for escapes and backreferences is ASCII-oriented.
        if (radix <= 0) return -1;

        int v = -1;
        if (c >= static_cast<char_type>('0') && c <= static_cast<char_type>('9')) {
            v = static_cast<int>(c - static_cast<char_type>('0'));
        } else if (c >= static_cast<char_type>('a') && c <= static_cast<char_type>('z')) {
            v = 10 + static_cast<int>(c - static_cast<char_type>('a'));
        } else if (c >= static_cast<char_type>('A') && c <= static_cast<char_type>('Z')) {
            v = 10 + static_cast<int>(c - static_cast<char_type>('A'));
        }

        return (v >= 0 && v < radix) ? v : -1;
    }

    locale_type imbue(locale_type l) {
        m_locale = l;
        return l;
    }

    locale_type getloc() const { return m_locale; }

private:
    locale_type m_locale = 0;
};

} // namespace lstring_re

#endif // LSTRING_RE_ICU_TRAITS_HXX
