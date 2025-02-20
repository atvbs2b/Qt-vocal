import sys
import json
import os
import webbrowser
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton, QTableWidget,
    QTableWidgetItem, QWidget, QLineEdit, QHBoxLayout, QListWidget,
    QAbstractItemView, QLabel, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

DATA_FILE = "songs_data.json"  # 保存するファイル名

class VocaloidManager(QMainWindow):
  def __init__(self):
    super().__init__()
    self.setWindowTitle("ボカロ管理")
    self.setGeometry(100, 100, 700, 400)

    self.songs_data = []
    self.central_widget = QWidget()
    self.setCentralWidget(self.central_widget)
    layout = QVBoxLayout(self.central_widget)

    # テーマ選択のボタンとラベル
    theme_layout = QHBoxLayout()
    theme_label = QLabel("テーマ")
    theme_layout.addWidget(theme_label)
    theme_names = ["Miku", "Rin", "Len", "Luka", "MEIKO", "KAITO"]
    theme_colors = {
        "Miku": "#39C5BB", "Rin": "orange", "Len": "#FFE211",
        "Luka": "pink", "MEIKO": "#D80000", "KAITO": "blue"
    }

    for theme, color in theme_colors.items():
      button = QPushButton("●")
      button.setFixedSize(30, 30)  # ボタンのサイズを小さくする
      button.setStyleSheet(
          f"background-color: {color}; border-radius: 15px;")
      button.setToolTip(theme)  # ボタンにマウスを乗せるとボカロ名が表示される
      button.clicked.connect(lambda _, t=theme: self.apply_theme(t))
      theme_layout.addWidget(button)

    layout.addLayout(theme_layout)

    # フィルター
    self.filter_song_input = QLineEdit(placeholderText="曲名で絞り込み")
    self.filter_producer_input = QLineEdit(placeholderText="ボカロP名で絞り込み")
    self.filter_vocal_input = QLineEdit(placeholderText="歌唱ボカロで絞り込み")
    self.filter_song_input.textChanged.connect(self.filter_songs)
    self.filter_producer_input.textChanged.connect(self.filter_songs)
    self.filter_vocal_input.textChanged.connect(self.filter_songs)

    layout.addWidget(self.filter_song_input)
    layout.addWidget(self.filter_producer_input)
    layout.addWidget(self.filter_vocal_input)

    # フィルタリセットボタン
    self.reset_filter_button = QPushButton("フィルタリセット")
    self.reset_filter_button.clicked.connect(self.reset_filters)
    layout.addWidget(self.reset_filter_button)

    # テーブル
    self.table = QTableWidget()
    self.table.setColumnCount(5)
    self.table.setHorizontalHeaderLabels(
        ["曲名", "ボカロP", "歌唱ボカロ", "リンク", "再生"])
    self.table.setSortingEnabled(True)
    layout.addWidget(self.table)

    # 入力フォーム
    input_layout = QHBoxLayout()
    self.song_input = QLineEdit(placeholderText="曲名")
    self.producer_input = QLineEdit(placeholderText="ボカロP")
    self.vocal_list = QListWidget()
    self.vocal_list.addItems([
        "初音ミク", "鏡音リン", "鏡音レン", "巡音ルカ", "MEIKO", "KAITO",
        "重音テト", "IA", "GUMI", "可不", "flower", "歌愛ユキ"
    ])
    self.vocal_list.setSelectionMode(QAbstractItemView.MultiSelection)
    self.custom_vocal_input = QLineEdit(placeholderText="その他のボカロ（カンマ区切り）")
    self.link_input = QLineEdit(placeholderText="楽曲リンク（URL）")
    self.add_button = QPushButton("追加")
    self.add_button.clicked.connect(self.add_song)

    input_layout.addWidget(self.song_input)
    input_layout.addWidget(self.producer_input)
    input_layout.addWidget(self.vocal_list)
    input_layout.addWidget(self.custom_vocal_input)
    input_layout.addWidget(self.link_input)
    input_layout.addWidget(self.add_button)
    layout.addLayout(input_layout)

    # 削除ボタン
    self.delete_button = QPushButton("選択した曲を削除")
    self.delete_button.clicked.connect(self.delete_song)
    layout.addWidget(self.delete_button)

    self.load_data()

  def apply_theme(self, theme):
    theme_colors = {
        "Miku": "#39C5BB", "Rin": "orange", "Len": "#FFE211",
        "Luka": "pink", "MEIKO": "#D80000", "KAITO": "blue"
    }
    main_color = theme_colors.get(theme, "#39C5BB")  # デフォルトをMikuの色に
    sub_color = main_color  # サブカラーもメインカラーと同じに設定

    self.setStyleSheet(f"""
            QMainWindow {{ background-color: {sub_color}; }}
            QLabel, QLineEdit, QTableWidget {{ color: black; }}
            QPushButton {{
                background-color: {main_color};
                color: white;
                border-radius: 15px;  /* 丸いボタン */
                padding: 10px;        /* ボタン内のスペース */
            }}
            QPushButton:hover {{
                background-color: #555;  /* ホバー時の色 */
            }}
            QTableWidget {{
                gridline-color: black;
                background-color: white;
            }}
            QHeaderView::section {{
                background-color: {main_color};
                color: white;
            }}
        """)

  def add_song(self):
    song_name = self.song_input.text().strip()
    producer_name = self.producer_input.text().strip()
    selected_vocals = [item.text()
                       for item in self.vocal_list.selectedItems()]
    custom_vocal = self.custom_vocal_input.text().strip()
    song_link = self.link_input.text().strip()

    if custom_vocal:
      selected_vocals.extend(
          [v.strip() for v in custom_vocal.split(",") if v.strip()]
      )
    vocal_names = " / ".join(selected_vocals)

    if song_name and producer_name and vocal_names:
      self.songs_data.append(
          [song_name, producer_name, vocal_names, song_link])
      self.save_data()
      self.update_table()
      self.song_input.clear()
      self.producer_input.clear()
      self.custom_vocal_input.clear()
      self.link_input.clear()
      self.vocal_list.clearSelection()

  def delete_song(self):
    selected_rows = sorted(
        set(index.row() for index in self.table.selectedIndexes()), reverse=True
    )

    if not selected_rows:
      # 何も選択されていない場合は何もしない
      QMessageBox.warning(self, "警告", "削除する曲が選択されていません。")
      return

    # 確認ダイアログを表示
    reply = QMessageBox.question(self, "確認",
                                 "選択した曲を本当に削除しますか？",
                                 QMessageBox.Yes | QMessageBox.No,
                                 QMessageBox.No)

    if reply == QMessageBox.Yes:
      # ユーザーが「はい」を選択した場合、削除処理を続行
      for row in selected_rows:
        del self.songs_data[row]
      self.save_data()
      self.update_table()
    else:
      # ユーザーが「いいえ」を選択した場合は何もしない
      return

  def update_table(self):
    """テーブル全体を songs_data に合わせて再描画"""
    self.table.setRowCount(0)
    for row, (song_name, producer_name, vocal_names, song_link) in enumerate(self.songs_data):
      self.table.insertRow(row)
      self.table.setItem(row, 0, QTableWidgetItem(song_name))
      self.table.setItem(row, 1, QTableWidgetItem(producer_name))
      self.table.setItem(row, 2, QTableWidgetItem(vocal_names))
      self.table.setItem(row, 3, QTableWidgetItem(song_link))

      # リンクを直接ボタンに渡す
      play_button = QPushButton("▶")
      # ここがポイント：lambda のデフォルト引数に song_link を渡す
      play_button.clicked.connect(
          lambda _, link=song_link: webbrowser.open(link))
      self.table.setCellWidget(row, 4, play_button)

  def filter_songs(self):
    song_filter = self.filter_song_input.text().lower()
    producer_filter = self.filter_producer_input.text().lower()
    vocal_filter = self.filter_vocal_input.text().lower()

    # フィルターされたデータを取得
    filtered_data = [
        (song_name, producer_name, vocal_names, song_link)
        for song_name, producer_name, vocal_names, song_link in self.songs_data
        if (song_filter in song_name.lower() and
            producer_filter in producer_name.lower() and
            vocal_filter in vocal_names.lower())
    ]

    # テーブルを更新
    self.table.setRowCount(0)
    for row, (song_name, producer_name, vocal_names, song_link) in enumerate(filtered_data):
      self.table.insertRow(row)
      self.table.setItem(row, 0, QTableWidgetItem(song_name))
      self.table.setItem(row, 1, QTableWidgetItem(producer_name))
      self.table.setItem(row, 2, QTableWidgetItem(vocal_names))
      self.table.setItem(row, 3, QTableWidgetItem(song_link))

      # リンクを直接ボタンに渡す
      play_button = QPushButton("▶")
      play_button.clicked.connect(
          lambda _, link=song_link: webbrowser.open(link))
      self.table.setCellWidget(row, 4, play_button)

    # ソートのために、ヘッダクリックを再度結び直す（毎回やるとやや冗長ですが簡単です）
    self.table.horizontalHeader().sectionClicked.connect(self.sort_table)

  def sort_table(self, logicalIndex):
    """並べ替えを行った後にフィルタリングを再適用する"""
    self.filter_songs()

  def reset_filters(self):
    """フィルタ入力をクリアして全データを再表示"""
    self.filter_song_input.clear()
    self.filter_producer_input.clear()
    self.filter_vocal_input.clear()
    self.load_data()  # 全データを再読込 → update_table() が呼ばれて表示更新

  def save_data(self):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
      json.dump(self.songs_data, f, ensure_ascii=False, indent=4)

  def load_data(self):
    if os.path.exists(DATA_FILE):
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        self.songs_data = json.load(f)
      self.update_table()

def main():
  app = QApplication(sys.argv)
  window = VocaloidManager()
  window.show()
  sys.exit(app.exec())

if __name__ == "__main__":
  main()
