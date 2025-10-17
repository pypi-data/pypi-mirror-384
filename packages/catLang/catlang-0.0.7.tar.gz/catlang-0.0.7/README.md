catLang is a solo programming language made for Python. It transpiles CatLang to Python and can run code via `.exc` (string) or `.exec_file` (file path).

```python
import catLang

# Execute CatLang code from a string
catLang.exc("""
for(let i=0,i<=50,i++){
    if(i%5==0){
        println(i)
    }
}
""")

# Execute a .cat source file
catLang.exec_file("Path\\To\\File.cat")
```

```cat
for(let  i=0,i<=50,i++){
    if(i%5==0){
        println(i)
    }
} // example code
```