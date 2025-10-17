import re

from keyweave.print.based_int import BasedInt

marker = "+-"


def get_pattern():
    escaped_pattern = re.escape(marker)
    pattern = rf"{escaped_pattern}(.*?){escaped_pattern}"
    return pattern


_percent_pat = re.compile(get_pattern())


class UnicodeEncoder:
    _char_to_code = dict[str, str]()
    _code_to_char = dict[str, str]()
    _last_id = BasedInt()

    def _register_char(self, ch: str) -> str:
        if ch not in self._char_to_code:
            self._last_id += 1
            self._char_to_code[ch] = str(self._last_id)
            self._code_to_char[self._char_to_code[ch]] = ch
        return self._char_to_code[ch]

    def get_len_of_decoded_string(self, s: str) -> int:
        return len(_percent_pat.sub("", s)) + len(_percent_pat.findall(s))

    def _should_encode(self, ch: str) -> bool:
        cp = ord(ch)
        return not (0x20 <= cp < 0x7F) or cp in (0x1B,)  # encode non-ASCII

    def _decode(self, code: str) -> str | None:
        return self._code_to_char.get(code, None)

    def to_(self, s: str) -> str:
        out = list[str]()
        for ch in s:
            if not self._should_encode(ch):  # keep ASCII as-is
                out.append(ch)
            else:
                out.append(self._register_char(ch).join((marker, marker)))
        return "".join(out)

    def from_(self, s: str) -> str:
        def repl(m: re.Match[str]) -> str:
            deciphered = self._decode(m.group(1))
            if deciphered is None:
                assert False, "Internal error: unknown code"
            return deciphered

        return _percent_pat.sub(repl, s)
