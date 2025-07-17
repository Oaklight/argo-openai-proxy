import difflib

text1 = "line1\nline2\nline3"
text2 = "line1\nline2 edited\nline3"

# differ = difflib.HtmlDiff()
# html_diff = differ.make_file(text1.splitlines(), text2.splitlines(), fromdesc='Original', todesc='Modified')

differ = difflib.ndiff(text1.splitlines(), text2.splitlines())
for line in differ:
    print(line)

differ = difflib.context_diff(text1.splitlines(), text2.splitlines())
for line in differ:
    print(line)

differ = difflib.unified_diff(text1.splitlines(), text2.splitlines())
for line in differ:
    print(line)

# with open('diff.html', 'w') as f:
#     f.write(html_diff)
