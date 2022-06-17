from os.path import join


class rF2RfM():
  def __init__(self, path: str):
    self.sections = []
    # TODO: PATHS
    self.load(path)
  def get_content(self):
    content = ""
    for section, props in self.sections.items():
      spacer = ""
      if section != "root":
        content += f"{section}\n"
        content += "{\n"
        spacer   = "\t"
      
      for prop in props:
        key = prop["key"]
        value = prop["value"]
        content += f"{spacer}{key}={value}\n"
      
      if section != "root":
        content += "}\n"
    return content

  def write(self, path: str):
    content = self.get_content()
    with open(path, "w") as file:
      file.write(content)

  def load(self, path: str):
    self.sections = []
    contents = open(path, "r").readlines()
    sections = {"root": []}
    current_section = "root"
    control_chars = ["{", "}"]
    for index, line in enumerate(contents):
      is_last = index == len(contents) -1
      next_line = contents[index+1] if not is_last else None

      cleaned_line = line.strip()
      if next_line and "{" in next_line:
        current_section = cleaned_line
        sections[current_section] = []
      else:
        if cleaned_line not in control_chars:
          # get rid of comments 
          comment_parts = cleaned_line.split("//")
          ignore_all = len(comment_parts) > 1 or len(cleaned_line) == 0

          final_line = comment_parts[0]

          if not ignore_all:
            key_value_split = final_line.split("=")
            key = key_value_split[0].strip().lstrip()
            value = key_value_split[1].strip().lstrip()
            sections[current_section].append({
              "key": key,
              "value": value
            })
      if next_line and "}" in next_line:
        current_section = "root"
    self.sections = sections