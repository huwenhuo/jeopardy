# Jeopardy Game in Python (Pygame)

A Python implementation of Jeopardy using **Pygame**, supporting two types of question sources:

1. **Custom TSV/CSV file** with multiple choice options.
2. **GitHub Jeopardy dataset** (`jeopardy_clues.csv` / `.tsv`).

---

## Requirements

* Python 3.10+
* Pygame 2.6.1+

Install Pygame if you don’t have it:

```bash
pip install pygame
```

---

## Files

* `jeopardy.py` – Main game script using a **custom question file**.
* `jeopardy_question.py` – Main game script using **GitHub Jeopardy dataset**.
* `questions.tsv` – Example custom file with multiple choice questions.
* `jeopardy_clues.csv` – GitHub dataset (download from [here](https://github.com/joshualohr/jeopardy)).

---

## File Formats

### Custom TSV/CSV (`jeopardy.py`)

| Column          | Description                                   |
| --------------- | --------------------------------------------- |
| subtype         | Category or topic                             |
| question        | Question text                                 |
| option1–option4 | Multiple choice options                       |
| correct         | Index of the correct option (1–4)             |
| time            | Time limit for the question in seconds        |
| square_text     | Points shown on the board (e.g., 100, 200, …) |

Example:

```
Minecraft	What is the max bookshelves for level 30 enchant?	14	15	16	12	3	20	100
```

---

### GitHub Jeopardy Dataset (`jeopardy_question.py`)

| Column             | Description                                              |
| ------------------ | -------------------------------------------------------- |
| round              | Round number for that air date                           |
| clue_value         | Points value of the clue                                 |
| daily_double_value | Daily double points (usually 0)                          |
| category           | Category name                                            |
| comments           | Optional comments                                        |
| answer             | Question text (in the dataset this is actually the clue) |
| question           | Correct answer (the "solution")                          |
| air_date           | Air date of the episode                                  |
| notes              | Any notes                                                |

Example:

```
1	100	0	LAKES & RIVERS		River mentioned most often in the Bible	the Jordan	1984-09-10
```

**Note:** In this dataset, the `answer` column contains the **question text**, and the `question` column contains the **answer**.

---

## Usage

### Using a Custom File (Multiple Choice)

```bash
python jeopardy.py questions.tsv
```

### Using GitHub Jeopardy Dataset

```bash
python jeopardy_question.py jeopardy_clues.csv
```

## License

This project is free to use and modify.
