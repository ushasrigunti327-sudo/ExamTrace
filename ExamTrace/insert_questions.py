from models.database import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

questions = [

(
"Who developed Python?",
"Dennis Ritchie",
"Guido van Rossum",
"James Gosling",
"Bjarne Stroustrup",
"Guido van Rossum"
),

(
"Which keyword is used to create a function?",
"class",
"function",
"def",
"fun",
"def"
),

(
"Which data type stores True or False?",
"int",
"bool",
"list",
"string",
"bool"
),

(
"Which symbol is used for comments?",
"//",
"#",
"/* */",
"--",
"#"
),

(
"Which loop repeats until a condition becomes false?",
"if",
"while",
"switch",
"class",
"while"
),

(
"Which function displays output?",
"input()",
"print()",
"display()",
"show()",
"print()"
),

(
"Which collection is mutable?",
"tuple",
"list",
"set",
"string",
"list"
),

(
"What is the extension of Python files?",
".java",
".cpp",
".py",
".html",
".py"
),

(
"Which keyword is used for conditions?",
"if",
"for",
"while",
"class",
"if"
),

(
"Which keyword returns a value from a function?",
"stop",
"exit",
"return",
"break",
"return"
)

]

cursor.executemany("""

INSERT INTO questions(

question,
option1,
option2,
option3,
option4,
correct_answer

)

VALUES(?,?,?,?,?,?)

""", questions)

conn.commit()
conn.close()

print("Questions inserted successfully.")