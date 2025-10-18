E is a solo programming language made for Python. It transpiles E to Python and can run code via `.exec` (string) or `.exec_file` (file path).

```python
import catLang

# Execute CatLang code from a string
catLang.exc("""
for(i in 1 ... 50):
    if(i%5==0):
        println(i)
    end;
end;
""")

# Execute a .cat source file
catLang.exec_file(r"Path\To\File.cat")
```

```csharp
for(i in 1 ... 5):
    if(i%5==0):
        println(i)
    end;
end; // example code
```