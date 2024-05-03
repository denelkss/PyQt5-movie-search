import sqlite3
import sys

from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidgetItem, QInputDialog


class MovieLibrary(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("design.ui", self)
        self.con = sqlite3.connect("movies_recom.sqlite")

        self.setFixedSize(1224, 800)

        # search (1 страница)
        self.button_search.clicked.connect(self.func_search)

        self.idEdit.setReadOnly(True)
        self.titleEdit.setReadOnly(True)
        self.genresEdit.setReadOnly(True)
        self.ratingEdit.setReadOnly(True)
        self.tagEdit.setReadOnly(True)
        self.imdbEdit.setReadOnly(True)
        self.tmdbEdit.setReadOnly(True)

        # recommendations (2 страница)
        self.idEdit_2.setReadOnly(True)
        self.titleEdit_2.setReadOnly(True)
        self.genresEdit_2.setReadOnly(True)
        self.ratingEdit_2.setReadOnly(True)

        self.selection_2.addItems(['Genre', 'Tag'])
        self.button_search_2.clicked.connect(self.func_recommendations)

        # my movies (3 страница)
        self.add_button.clicked.connect(self.add_movies)
        self.func_my_movies()

        # открытие инструкций
        self.instructionsButton.clicked.connect(self.instructions_1)
        self.instructionsButton_2.clicked.connect(self.instructions_2)
        self.instructionsButton_3.clicked.connect(self.instructions_3)

    def instructions_1(self):
        msg_inst = QMessageBox()

        msg_inst.setText("""
        В верхнем поле введите название фильма (на английском),
        информацию о котором хотели бы получить в полях ниже.""")
        msg_inst.setInformativeText("Это может занять некоторое время.")
        msg_inst.setWindowTitle("Инструкция")

        msg_inst.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg_inst.exec_()

    def instructions_2(self):
        msg_inst2 = QMessageBox()

        msg_inst2.setText("""
        Выберите один из предложенных пунктов сверху (поиск по жанру/тегу).
        Далее в верхнем поле введите жанр или тег,
        исходя из которых хотели бы получить результаты (несколько с фильмов с наиболее хорошим рейтингом)""")
        msg_inst2.setInformativeText("Это может занять некоторое время.")
        msg_inst2.setWindowTitle("Инструкция")

        msg_inst2.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg_inst2.exec_()

    def instructions_3(self):
        msg_inst3 = QMessageBox()

        msg_inst3.setText("""
        Для добавления фильма в просмотренные нажмите на кнопку сверху.
        Далее в открывшемся окне введите назвние просмотренного фильма.
        Результаты появятся в таблице""")
        msg_inst3.setInformativeText("Это может занять некоторое время.")
        msg_inst3.setWindowTitle("Инструкция")

        msg_inst3.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msg_inst3.exec_()

    def func_search(self):
        try:
            cur = self.con.cursor()
            data = self.selectionEdit.text()
            if data == '':
                raise ValueError
            result = cur.execute(f"""SELECT * FROM movies 
            WHERE title LIKE '%{data}%'""").fetchall()
            title = cur.execute(f"""SELECT title FROM movies
            WHERE title LIKE '%{data}%'""").fetchall()
            title = ''.join(title[0])

            if len(result) > 1:
                result = list(result[0])
                result = list(map(str, result))
            else:
                result = list(map(str, *result))

            rating = cur.execute(f"""SELECT AVG(rating) FROM ratings
            WHERE movie_id=(SELECT id_movie FROM movies WHERE title='{title}')""").fetchall()
            res_rating = str(round(*list(map(float, *rating)), 1))

            tag = cur.execute(f"""SELECT tag FROM tags
            WHERE movie_id=(SELECT id_movie FROM movies WHERE title='{title}')""").fetchall()
            res_tag = '|'.join([str(*i) for i in tag])

            imdb_id = cur.execute(f"""SELECT imdb_id FROM links
            WHERE movie_id=(SELECT id_movie FROM movies WHERE title='{title}')""").fetchall()
            res_imdb = str(*list(map(int, *imdb_id)))

            tmdb_id = cur.execute(f"""SELECT tmdb_id FROM links
            WHERE movie_id=(SELECT id_movie FROM movies WHERE title='{title}')""").fetchall()
            res_tmdb = str(*list(map(int, *tmdb_id)))

            self.idEdit.setText(result[0])
            self.titleEdit.setText(result[1])
            self.genresEdit.setText(result[2])
            self.ratingEdit.setText(res_rating)
            self.tagEdit.setText(res_tag)
            self.imdbEdit.setText(res_imdb)
            self.tmdbEdit.setText(res_tmdb)

        except ValueError:
            # всплывающее окно при неверном вводе (пусто)
            msg_error = QMessageBox()
            msg_error.setIcon(QMessageBox.Information)

            msg_error.setText("Incorrect input")
            msg_error.setInformativeText("Try again")
            msg_error.setWindowTitle("Error")
            msg_error.setDetailedText('Error: "Empty input field"')

            msg_error.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg_error.exec_()

        except Exception:
            # всплывающее окно при неверном вводе (ничего не найдено)
            msg_error = QMessageBox()
            msg_error.setIcon(QMessageBox.Information)

            msg_error.setText("Nothing found")
            msg_error.setInformativeText("Try again")
            msg_error.setWindowTitle("Error")
            msg_error.setDetailedText('Error: "Nothing found"')

            msg_error.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg_error.exec_()

    def func_recommendations(self):
        try:
            cur = self.con.cursor()
            result_dict = {}
            data2 = self.selectionEdit_2.text()
            if data2 == '':
                raise ValueError
            # Поиск по жанру
            if self.selection_2.currentText() == 'Genre':
                lst = cur.execute(f"SELECT * FROM movies WHERE genres LIKE '%{data2}%'").fetchall()
            # Поиск по тэгу
            elif self.selection_2.currentText() == 'Tag':
                lst = cur.execute(f"""SELECT * FROM movies
                WHERE id_movie IN (SELECT movie_id FROM tags WHERE tag LIKE '{data2}%')""").fetchall()
            self.calculate_rating(lst, result_dict)

            # основной результат
            result_dict = sorted(result_dict.items(), key=lambda item: item[1], reverse=True)
            result_rating = list(result_dict[0])
            id = result_rating[0]
            result = cur.execute(f"SELECT * FROM movies WHERE id_movie={id}").fetchall()
            result = list(map(str, list(result[0])))

            self.idEdit_2.setText(result[0])
            self.titleEdit_2.setText(result[1])
            self.genresEdit_2.setText(result[2])
            self.ratingEdit_2.setText(str(result_rating[1]))
            self.label.setText('Other:')

            # результаты в таблице
            table_result = result_dict[1:]
            row = 0
            col = 0
            for el in table_result:
                el = list(el)
                tab_res = cur.execute(f"SELECT * FROM movies WHERE id_movie={el[0]}").fetchall()
                tab_res = list(map(str, list(list(tab_res[0]))))

                self.table.setItem(row, col, QTableWidgetItem(tab_res[1]))
                self.table.setItem(row, col + 1, QTableWidgetItem(tab_res[2]))
                self.table.setItem(row, col + 2, QTableWidgetItem(str(el[1])))
                row += 1

        except ValueError:
            # всплывающее окно при неверном вводе (пусто)
            msg_error = QMessageBox()
            msg_error.setIcon(QMessageBox.Information)

            msg_error.setText("Incorrect input")
            msg_error.setInformativeText("Try again")
            msg_error.setWindowTitle("Error")
            msg_error.setDetailedText('Error: "Empty input field"')

            msg_error.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg_error.exec_()

        except Exception:
            # всплывающее окно при неверном вводе (ничего не найдено)
            msg_error = QMessageBox()
            msg_error.setIcon(QMessageBox.Information)

            msg_error.setText("Nothing found")
            msg_error.setInformativeText("Try again")
            msg_error.setWindowTitle("Error")
            msg_error.setDetailedText('Error: "Nothing found"')

            msg_error.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg_error.exec_()

    # рассчитать рейтинг
    def calculate_rating(self, lst, result_dict):
        cur = self.con.cursor()

        for el in lst:
            el = list(el)
            id = el[0]
            rating = cur.execute(f"SELECT AVG(rating) FROM ratings WHERE movie_id={id}").fetchall()
            rating = round(*list(map(float, *rating)), 1)
            if rating >= 3.0:
                result_dict[id] = rating
                if len(result_dict) == 6:
                    break

    # добавление в бд и таблицу нового фильма
    def add_movies(self):
        try:
            cur = self.con.cursor()
            title, ok = QInputDialog.getText(self, 'Add movie', 'Enter the name of the movie')
            if not ok:
                return
            result = cur.execute(f"SELECT * FROM movies WHERE title LIKE '%{title}%'").fetchall()
            if len(result) > 1:
                result = list(map(str, list(result[0])))
            else:
                result = list(map(str, *result))
            cur.execute(f"""INSERT INTO my_movies (id, title, genre)
            VALUES ({result[0]}, '{result[1]}', '{result[2]}');""")
            table_result = cur.execute("""SELECT * FROM my_movies""").fetchall()
            count_movies = len(table_result) - 1

            self.moviesTable.insertRow(count_movies)
            self.moviesTable.setItem(count_movies, 0, QTableWidgetItem(str(result[0])))
            self.moviesTable.setItem(count_movies, 1, QTableWidgetItem(result[1]))
            self.moviesTable.setItem(count_movies, 2, QTableWidgetItem(result[2]))

            self.con.commit()

        except Exception:
            msg_error = QMessageBox()
            msg_error.setIcon(QMessageBox.Information)

            msg_error.setText("Unknown Error")
            msg_error.setInformativeText("Try again")
            msg_error.setWindowTitle("Error")

            msg_error.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg_error.exec_()

    # добавление всех уже известных просмотренные фильмов при открытии
    def func_my_movies(self):
        cur = self.con.cursor()
        table_result = cur.execute("""SELECT * FROM my_movies""").fetchall()
        count = 0
        for el in table_result:
            self.moviesTable.insertRow(count)
            self.moviesTable.setItem(count, 0, QTableWidgetItem(str(el[0])))
            self.moviesTable.setItem(count, 1, QTableWidgetItem(el[1]))
            self.moviesTable.setItem(count, 2, QTableWidgetItem(el[2]))
            count += 1
        self.con.commit()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MovieLibrary()
    ex.show()
    sys.exit(app.exec())
