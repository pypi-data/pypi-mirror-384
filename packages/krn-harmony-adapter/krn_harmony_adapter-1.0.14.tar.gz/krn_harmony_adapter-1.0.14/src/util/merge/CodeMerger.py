# -*- coding: utf-8 -*-
import re
import textwrap
import difflib
from typing import Dict, Set, List, Tuple

class CodeMerger:
    """
    一个最终版的、用于智能合并 RN 和 Harmony 代码的工具。
    它集成了作用域感知解析、依赖分析和基于规则的差异合并引擎。
    """
    JS_KEYWORDS = {
        'if', 'for', 'while', 'switch', 'case', 'catch', 'throw', 'try', 'finally', 'return', 'yield', 'await', 'async', 'function', 'class', 'const', 'let', 'var', 'import', 'export', 'default', 'from', 'in', 'of', 'new', 'delete', 'typeof', 'instanceof', 'void', 'with', 'debugger', 'super', 'this', 'get', 'set', 'console', 'Math', 'JSON', 'Promise', 'Object', 'Array', 'String', 'Number', 'Boolean', 'Date', 'RegExp', 'Map', 'Set', 'WeakMap', 'WeakSet', 'Symbol', 'parseInt', 'parseFloat', 'isNaN', 'isFinite', 'encodeURI', 'decodeURI', 'encodeURIComponent', 'decodeURIComponent', 'require'
    }

    def _get_brace_level_at(self, content: str, pos: int) -> int:
        """通过逐字符扫描，准确计算在特定位置的括号嵌套层级，会忽略字符串和注释内的括号。"""
        level, in_string, in_line_comment, in_block_comment, i = 0, None, False, False, 0
        while i < pos:
            char = content[i]
            prev_char = content[i-1] if i > 0 else ''
            if in_line_comment:
                if char == '\n': in_line_comment = False
            elif in_block_comment:
                if char == '*' and content[i-1:i+1] == '*/': in_block_comment = False
            elif in_string:
                if char == in_string and prev_char != '\\': in_string = None
            else:
                if char in ['"', "'", "`"]: in_string = char
                elif char == '/' and content[i-1:i+1] == '//': in_line_comment = True
                elif char == '*' and content[i-1:i+1] == '/*': in_block_comment = True
                elif char == '{': level += 1
                elif char == '}': level -= 1
            i += 1
        return level

    def _extract_top_level_blocks(self, content: str) -> Tuple[List[Tuple[str, str]], Dict[str, str]]:
        """使用作用域感知的方法，只提取顶层的代码块。"""
        ordered_blocks, blocks_dict = [], {}
        block_start_pattern = re.compile(r"(?:export\s+)?(?:const|let|var|function|class)\s+(\w+)")
        
        current_pos = 0
        while current_pos < len(content):
            match = block_start_pattern.search(content, pos=current_pos)
            if not match: break

            if self._get_brace_level_at(content, match.start()) == 0:
                block_name = match.group(1)
                if block_name in blocks_dict:
                    current_pos = match.end()
                    continue
                start_pos, end_pos = match.start(), self._find_block_end(content, match.end())
                block_content = content[start_pos:end_pos]
                ordered_blocks.append((block_name, block_content))
                blocks_dict[block_name] = block_content
                current_pos = end_pos
            else:
                current_pos = match.end()
        return ordered_blocks, blocks_dict
    
    def _find_function_calls(self, content: str) -> Set[str]:
        pattern = re.compile(r"(?<!\.)\b([a-zA-Z_$][\w$]*)\s*\(")
        return set(pattern.findall(content)) - self.JS_KEYWORDS

    def _find_identifier_usages(self, content: str) -> Set[str]:
        pattern = re.compile(r"\b([a-zA-Z_$][\w$]*)\b")
        return set(pattern.findall(content)) - self.JS_KEYWORDS

    def _find_block_end(self, content: str, start_pos: int) -> int:
        try:
            first_brace_pos = content.index('{', start_pos)
        except ValueError:
            try: return content.index(';', start_pos) + 1
            except ValueError:
                try: return content.index('\n', start_pos) + 1
                except ValueError: return len(content)
        brace_level, search_pos = 1, first_brace_pos + 1
        while brace_level > 0 and search_pos < len(content):
            char = content[search_pos]
            if char == '{': brace_level += 1
            elif char == '}': brace_level -= 1
            search_pos += 1
        try:
            semicolon_after_brace = content.index(';', search_pos - 1)
            if all(c.isspace() for c in content[search_pos:semicolon_after_brace]): return semicolon_after_brace + 1
        except ValueError: pass
        return search_pos

    def _extract_imports(self, content: str) -> Dict[str, str]:
        imports_map = {}
        import_lines = re.findall(r"^\s*(?:import|from)\s+.*?(?:;|$)", content, re.MULTILINE)
        for line in import_lines:
            normalized_line = line.strip().rstrip(';')
            if ' from ' in normalized_line and normalized_line.startswith('import'):
                match = re.search(r"import\s+(.*?)\s+from", normalized_line)
                if not match: continue
                imports_str = match.group(1).strip()
                if imports_str.startswith('{') and imports_str.endswith('}'):
                    imports_str = imports_str[1:-1]
                    components = [c.strip().split(' as ')[0] for c in imports_str.split(',')]
                    for component in filter(None, components): imports_map[component] = normalized_line
                elif '*' in imports_str:
                    ns_match = re.search(r"\*\s+as\s+(\w+)", imports_str)
                    if ns_match: imports_map[ns_match.group(1)] = normalized_line
                else:
                    default_import = imports_str.split(',')[0].strip()
                    if default_import and '{' not in default_import: imports_map[default_import] = normalized_line
                    if '{' in imports_str and '}' in imports_str:
                        named_match = re.search(r"\{(.*?)\}", imports_str)
                        if named_match:
                            named_str = named_match.group(1)
                            components = [c.strip().split(' as ')[0] for c in named_str.split(',')]
                            for component in filter(None, components): imports_map[component] = normalized_line
            elif ' import ' in normalized_line and normalized_line.startswith('from'):
                match = re.search(r"import\s+(.*)", normalized_line)
                if not match: continue
                imports_str = match.group(1).strip()
                if imports_str.startswith('{') and imports_str.endswith('}'): imports_str = imports_str[1:-1]
                components = [c.strip().split(' as ')[0] for c in imports_str.split(',')]
                for component in filter(None, components): imports_map[component] = normalized_line
        return imports_map
    
    def merge_code(self, current_content: str, backup_content: str) -> str:
        """
        主函数：使用最终的智能合并策略，保留 harmony 相关代码，并尽可能减少手动处理。
        """
        ordered_backup_blocks, all_backup_blocks = self._extract_top_level_blocks(backup_content)
        initial_harmony_blocks = {
            name: content for name, content in all_backup_blocks.items()
            if "harmony" in content
        }
        if not initial_harmony_blocks:
            print("INFO: 在 backup_content 中未发现 'harmony' 关键字，无需合并。")
            return current_content

        final_blocks_to_restore = initial_harmony_blocks.copy()
        work_queue = list(initial_harmony_blocks.keys())
        while work_queue:
            block_name_to_analyze = work_queue.pop(0)
            block_content = final_blocks_to_restore.get(block_name_to_analyze, "")
            all_potential_dependencies = self._find_function_calls(block_content).union(self._find_identifier_usages(block_content))
            for dep_name in all_potential_dependencies:
                if dep_name in all_backup_blocks and dep_name not in final_blocks_to_restore:
                    final_blocks_to_restore[dep_name] = all_backup_blocks[dep_name]
                    work_queue.append(dep_name)
        
        backup_imports_map = self._extract_imports(backup_content)
        required_imports_set: Set[str] = set()
        for block_content in final_blocks_to_restore.values():
            for component, line in backup_imports_map.items():
                if re.search(r'\b' + re.escape(component) + r'\b', block_content):
                    required_imports_set.add(line)
        current_import_lines_list = re.findall(r"^\s*(?:import|from)\s+.*(?:;|$)", current_content, re.MULTILINE)
        current_import_lines_set = set(line.strip().rstrip(';') for line in current_import_lines_list)
        imports_to_add = required_imports_set - current_import_lines_set
        new_content = current_content
        if imports_to_add:
            imports_to_add_str = "\n".join(sorted(list(imports_to_add)))
            if current_import_lines_list:
                last_import_line = current_import_lines_list[-1]
                last_import_pos = new_content.rfind(last_import_line) + len(last_import_line)
                new_content = new_content[:last_import_pos].rstrip() + "\n" + imports_to_add_str + new_content[last_import_pos:]
            else:
                new_content = imports_to_add_str + "\n\n" + new_content

        _, current_blocks_dict = self._extract_top_level_blocks(new_content)
        blocks_to_merge = {name: final_blocks_to_restore[name] for name in final_blocks_to_restore if name in current_blocks_dict}
        blocks_to_add = {name: final_blocks_to_restore[name] for name in final_blocks_to_restore if name not in current_blocks_dict}
        content_after_merge = new_content

        for name, backup_block_content in blocks_to_merge.items():
            current_block_content = current_blocks_dict[name]
            if current_block_content.strip() == backup_block_content.strip(): continue

            current_lines = current_block_content.splitlines()
            backup_lines = backup_block_content.splitlines()
            
            s = difflib.SequenceMatcher(None, current_lines, backup_lines, autojunk=False)
            merged_lines = []
            for tag, i1, i2, j1, j2 in s.get_opcodes():
                if tag == 'equal':
                    merged_lines.extend(current_lines[i1:i2])
                elif tag == 'insert':
                    merged_lines.extend(backup_lines[j1:j2])
                elif tag == 'delete':
                    merged_lines.extend(current_lines[i1:i2])
                elif tag == 'replace':
                    current_chunk = current_lines[i1:i2]
                    backup_chunk = backup_lines[j1:j2]
                    backup_chunk_str = "\n".join(backup_chunk)
                    
                    if "harmony" in backup_chunk_str:
                        sub_matcher = difflib.SequenceMatcher(None, current_chunk, backup_chunk, autojunk=False)
                        for sub_tag, sub_i1, sub_i2, sub_j1, sub_j2 in sub_matcher.get_opcodes():
                            if sub_tag in ['equal', 'delete']:
                                merged_lines.extend(current_chunk[sub_i1:sub_i2])
                            elif sub_tag in ['insert', 'replace']:
                                merged_lines.extend(backup_chunk[sub_j1:sub_j2])
                    else:
                        merged_lines.extend(current_chunk)
            
            merged_block_content = "\n".join(merged_lines)
            content_after_merge = content_after_merge.replace(current_block_content, merged_block_content, 1)

        final_content = content_after_merge
        ordered_blocks_to_add = [b for b in ordered_backup_blocks if b[0] in blocks_to_add]
        for name_to_add, content_to_add in ordered_blocks_to_add:
            _, current_blocks_in_final_content = self._extract_top_level_blocks(final_content)
            original_index = next((i for i, v in enumerate(ordered_backup_blocks) if v[0] == name_to_add), -1)
            insertion_point_found = False
            for i in range(original_index - 1, -1, -1):
                preceding_block_name = ordered_backup_blocks[i][0]
                if preceding_block_name in current_blocks_in_final_content:
                    anchor_content = current_blocks_in_final_content[preceding_block_name]
                    replacement = anchor_content + "\n\n" + content_to_add
                    final_content = final_content.replace(anchor_content, replacement, 1)
                    insertion_point_found = True
                    break
            if insertion_point_found: continue
            for i in range(original_index + 1, len(ordered_backup_blocks)):
                succeeding_block_name = ordered_backup_blocks[i][0]
                if succeeding_block_name in current_blocks_in_final_content:
                    anchor_content = current_blocks_in_final_content[succeeding_block_name]
                    replacement = content_to_add + "\n\n" + anchor_content
                    final_content = final_content.replace(anchor_content, replacement, 1)
                    insertion_point_found = True
                    break
            if not insertion_point_found:
                final_content = final_content.rstrip() + "\n\n" + content_to_add
        return final_content
