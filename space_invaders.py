import random
import tkinter as tk
from tkinter import messagebox


class ElectroQuestV2:

  def __init__(self, root):
    self.root = root
    self.root.title("ECE 2A: Board Exam Refresher")
    self.root.geometry("600x700")
    self.root.config(bg="#d8b4fe")

    self.score = 0
    self.level = 1
    self.game_state = "PLAYING"

    self.player_speed = 12
    self.bullet_speed = -18
    self.enemy_speed = 2
    self.enemy_direction = 1

    self.bullets = []
    self.enemies = []

    self.stages = [
        {
            "name": "Stage 1: Physics 2 ",
            "boss_q": (
                "What law states that the line integral of magnetic field"
                " around a closed loop is proportional to the electric"
                " current enclosed?"
            ),
            "choices": [
                "A) Gauss's Law",
                "B) Ampere's Law",
                "C) Faraday's Law",
                "D) Coulomb's Law",
            ],
            "correct": 1,
        },
        {
            "name": "Stage 2: Circuit Analysis",
            "boss_q": (
                "Which theorem replaces a linear active network with a"
                " single voltage source and series resistor?"
            ),
            "choices": [
                "A) Norton's Theorem",
                "B) Thevenin's Theorem",
                "C) Superposition Theorem",
                "D) Maximum Power Transfer",
            ],
            "correct": 1,
        },
        {
            "name": "Stage 3: Electronic Devices",
            "boss_q": "In which region does a Zener diode normally operate?",
            "choices": [
                "A) Forward active region",
                "B) Cutoff region",
                "C) Breakdown / Zener region",
                "D) Saturation region",
            ],
            "correct": 2,
        },
        {
            "name": "Stage 4: Communications",
            "boss_q": (
                "What modulation technique shifts the frequency of a carrier"
                " wave in accordance with the message signal?"
            ),
            "choices": [
                "A) Amplitude Modulation (AM)",
                "B) Frequency Modulation (FM)",
                "C) Phase Shift Keying (PSK)",
                "D) Pulse Code Modulation (PCM)",
            ],
            "correct": 1,
        },
        {
            "name": "Stage 5: Advanced Telecom (Final Boss to graduate)",
            "boss_q": (
                "Which multiple access technology is fundamental to 4G LTE and"
                " 5G wireless networks to avoid ISI?"
            ),
            "choices": [
                "A) CDMA",
                "B) TDMA",
                "C) FDMA",
                "D) OFDM "
                "(Orthogonal Frequency Division Multiplexing)",
            ],
            "correct": 3,
        },
    ]

    self.title_lbl = tk.Label(
        root,
        text="ECE Rise To The Top",
        font=("Bank Gothic", 18, "bold"),
        fg="#2a0845",
        bg="#d8b4fe",
    )
    self.title_lbl.pack(pady=5)

    self.info_frame = tk.Frame(root, bg="#d8b4fe")
    self.info_frame.pack(fill="x", padx=20)

    self.score_lbl = tk.Label(
        self.info_frame,
        text=f"Score: {self.score}",
        font=("Courier", 12, "bold"),
        fg="#2a0845",
        bg="#d8b4fe",
    )
    self.score_lbl.pack(side="left")

    self.stage_lbl = tk.Label(
        self.info_frame,
        text=self.stages[0]["name"],
        font=("Courier", 11, "bold"),
        fg="#990000",
        bg="#d8b4fe",
    )
    self.stage_lbl.pack(side="right")

    self.canvas = tk.Canvas(
        root,
        width=600,
        height=420,
        bg="#111118",
        highlightthickness=3,
        highlightbackground="#2a0845",
    )
    self.canvas.pack(pady=10)

    self.player = self.canvas.create_rectangle(
        275, 370, 325, 395, fill="#4d94ff", outline="white"
    )

    self.quiz_frame = tk.Frame(root, bg="#d8b4fe")

    self.quiz_question_lbl = tk.Label(
        self.quiz_frame,
        text="",
        font=("Courier", 11, "bold"),
        fg="#111118",
        bg="#d8b4fe",
        wraplength=550,
        justify="center",
    )
    self.quiz_question_lbl.pack(pady=5)

    self.choice_buttons = []
    for i in range(4):
      btn = tk.Button(
          self.quiz_frame,
          text="",
          font=("Courier", 10, "bold"),
          bg="#ffffff",
          fg="#2a0845",
          width=50,
          command=lambda idx=i: self.check_quiz_answer(idx),
      )
      btn.pack(pady=3)
      self.choice_buttons.append(btn)

    self.root.bind("<Left>", self.move_player)
    self.root.bind("<Right>", self.move_player)
    self.root.bind("<space>", lambda event: self.fire_bullet())

    self.create_enemies()
    self.game_loop()

  def create_enemies(self):
    for enemy in self.enemies:
      self.canvas.delete(enemy)
    self.enemies.clear()

    for i in range(3):
      for j in range(7):
        x1 = 40 + j * 75
        y1 = 40 + i * 35
        x2 = 100 + j * 75
        y2 = 70 + i * 35
        enemy = self.canvas.create_rectangle(
            x1, y1, x2, y2, fill="#ff4d4d", outline="yellow"
        )
        self.enemies.append(enemy)

  def move_player(self, event):
    if self.game_state != "PLAYING":
      return
    x = 0
    coords = self.canvas.coords(self.player)
    if event.keysym == "Left" and coords[0] > 0:
      x = -self.player_speed
    elif event.keysym == "Right" and coords[2] < 600:
      x = self.player_speed
    self.canvas.move(self.player, x, 0)

  def fire_bullet(self):
    if self.game_state != "PLAYING":
      return
    p_coords = self.canvas.coords(self.player)
    x1 = p_coords[0] + 22
    y1 = 360
    x2 = p_coords[2] - 22
    y2 = 345
    bullet = self.canvas.create_rectangle(
        x1, y1, x2, y2, fill="#55ff55", outline=""
    )
    self.bullets.append(bullet)

  def move_bullets(self):
    for bullet in self.bullets[:]:
      self.canvas.move(bullet, 0, self.bullet_speed)
      coords = self.canvas.coords(bullet)
      if coords and coords[1] < 0:
        self.canvas.delete(bullet)
        self.bullets.remove(bullet)

  def move_enemies(self):
    edge_reached = False
    for enemy in self.enemies:
      self.canvas.move(enemy, self.enemy_speed * self.enemy_direction, 0)
      coords = self.canvas.coords(enemy)
      if coords and (coords[2] >= 590 or coords[0] <= 10):
        edge_reached = True

    if edge_reached:
      self.enemy_direction *= -1
      for enemy in self.enemies:
        self.canvas.move(enemy, 0, 15)

  def check_collisions(self):
    for bullet in self.bullets[:]:
      b_coords = self.canvas.coords(bullet)
      if not b_coords:
        continue
      for enemy in self.enemies[:]:
        e_coords = self.canvas.coords(enemy)
        if not e_coords:
          continue
        if (
            b_coords[2] > e_coords[0]
            and b_coords[0] < e_coords[2]
            and b_coords[3] > e_coords[1]
            and b_coords[1] < e_coords[3]
        ):
          self.canvas.delete(bullet)
          self.canvas.delete(enemy)
          if bullet in self.bullets:
            self.bullets.remove(bullet)
          if enemy in self.enemies:
            self.enemies.remove(enemy)
          self.score += 50
          self.score_lbl.config(text=f"Score: {self.score}")
          break

    if len(self.enemies) == 0 and self.game_state == "PLAYING":
      self.trigger_boss_quiz()

  def trigger_boss_quiz(self):
    self.game_state = "QUIZ"
    for b in self.bullets:
      self.canvas.delete(b)
    self.bullets.clear()

    stage_data = self.stages[self.level - 1]
    self.quiz_question_lbl.config(
        text=f"HERE COMES THE MAJOR ({stage_data['name']}):\n"
        + stage_data["boss_q"]
    )
    for i in range(4):
      self.choice_buttons[i].config(text=stage_data["choices"][i])

    self.canvas.pack_forget()
    self.quiz_frame.pack(pady=10)

  def check_quiz_answer(self, idx):
    stage_data = self.stages[self.level - 1]
    if idx == stage_data["correct"]:
      self.score += 500
      self.score_lbl.config(text=f"Score: {self.score}")
      messagebox.showinfo(
          "Exam Passed!",
          "Correct! You're not going to petition this ECE level!\n+500 Points",
      )

      self.quiz_frame.pack_forget()
      self.canvas.pack(pady=10)

      self.level += 1
      if self.level > len(self.stages):
        self.game_state = "WIN"
        messagebox.showinfo(
            "Board Exam Topnotcher!",
            f"Congratulations! You cleared all ECE subjects!\nFinal Score:"
            f" {self.score}",
        )
        self.root.destroy()
      else:
        self.stage_lbl.config(text=self.stages[self.level - 1]["name"])
        self.enemy_speed += 0.8
        self.game_state = "PLAYING"
        self.create_enemies()
    else:
      messagebox.showerror(
          "Failed Exam", "Incorrect answer! Review your ECE formula notes!"
      )
      self.game_state = "GAMEOVER"
      messagebox.showinfo(
          "Game Over",
          f"You failed the board subject. Final Score: {self.score}",
      )
      self.root.destroy()

  def game_loop(self):
    if self.game_state == "PLAYING":
      self.move_bullets()
      self.move_enemies()
      self.check_collisions()

      for enemy in self.enemies:
        coords = self.canvas.coords(enemy)
        if coords and coords[3] >= 360:
          self.game_state = "GAMEOVER"
          messagebox.showinfo(
              "Game Over", f"Enemies breached! Final Score: {self.score}"
          )
          self.root.destroy()
          return

    if self.game_state != "GAMEOVER" and self.game_state != "WIN":
      self.root.after(40, self.game_loop)


if __name__ == "__main__":
  root = tk.Tk()
  game = ElectroQuestV2(root)
  root.mainloop()
