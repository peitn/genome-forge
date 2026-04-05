import re

class GenomePreprocessor:
    def extract_bodies(self, source_code: str) -> tuple[str, dict]:
        bodies: dict[str, str] = {}
        counter = 0
        pattern = re.compile(r'(behavior\s+\w+\s*\([^)]*\)\s*->\s*\w+\s*|on\s+\w+\s*\([^)]*\)\s*)\{')
        result_code = ""
        last_idx = 0
        while True:
            match = pattern.search(source_code, last_idx)
            if not match:
                result_code += source_code[last_idx:]
                break
            start_bracket_idx = match.end() - 1
            result_code += source_code[last_idx:start_bracket_idx]
            open_count = 0
            end_bracket_idx = -1
            for i in range(start_bracket_idx, len(source_code)):
                if source_code[i] == '{':
                    open_count += 1
                elif source_code[i] == '}':
                    open_count -= 1
                    if open_count == 0:
                        end_bracket_idx = i
                        break
            if end_bracket_idx == -1:
                raise SyntaxError("Unbalanced braces in DSL source!")
            raw_body = source_code[start_bracket_idx + 1:end_bracket_idx].strip("\r\n")
            lines = raw_body.split("\n")
            non_empty = [line for line in lines if line.strip()]
            if non_empty:
                min_indent = min(len(line) - len(line.lstrip()) for line in non_empty)
                cleaned = [line[min_indent:] if line.strip() else "" for line in lines]
                raw_body = "\n".join(cleaned)
            placeholder = f"__BODY_{counter}__"
            bodies[placeholder] = raw_body
            counter += 1
            result_code += placeholder
            last_idx = end_bracket_idx + 1
        return result_code, bodies
