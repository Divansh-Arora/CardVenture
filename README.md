# Cardventure — Technical Writeup

This document is a technical writeup for the Cardventure application.
This document uses Simplified Technical English (STE). STE uses short
sentences and simple words. STE helps all readers to understand the text.

Made with 💛 by **Divansh**

---

## 1. Introduction

Cardventure is a web application. Cardventure changes a PDF file into a
set of flashcards. Cardventure uses a study method called spaced
repetition. Spaced repetition shows a card again after a period of time.
The period of time gets longer when the user remembers the card well.

Cardventure has two main parts:

- The **backend**. The backend is a server. The server stores data and
  creates flashcards from a PDF file.
- The **frontend**. The frontend is a website. The user sees the
  frontend in a web browser. The user studies the flashcards on the
  frontend.

This document describes both parts. This document also gives steps to
install and run the application.

---

## 2. System Overview

The backend and the frontend work together. The frontend sends requests
to the backend. The backend sends data back to the frontend.

The diagram below shows the flow of data.

```
[ User's browser ]
        |
        | 1. User uploads a PDF file
        v
[ Frontend (React + Vite) ]
        |
        | 2. Frontend sends the file to the backend
        v
[ Backend (FastAPI) ]
        |
        | 3. Backend reads the PDF file
        | 4. Backend removes pages with no useful content
        | 5. Backend sends the text to an AI language model
        | 6. AI language model creates flashcards
        | 7. Backend checks and stores the flashcards
        v
[ Database ]
        |
        | 8. Backend sends the flashcards back to the frontend
        v
[ Frontend shows the flashcards to the user ]
```

---

## 3. The Backend

The backend uses the FastAPI framework. The backend uses the Python
programming language. The backend stores data in a database.

### 3.1 Main functions of the backend

The backend has these main functions:

1. **User accounts.** The backend lets a user register and log in. The
   backend gives the user a token. The frontend sends the token with
   each request. The token proves the identity of the user.

2. **PDF processing.** The backend reads the text on each page of a
   PDF file. The backend removes pages that are not useful. Examples of
   not useful pages are an index page, a table of contents, and an
   answer key.

3. **Card generation.** The backend groups the PDF text into sections.
   The backend sends each section to an AI language model. The AI
   language model writes flashcards for each section. Each flashcard has
   a question, an answer, a category, and a difficulty level.

4. **Card cleanup.** The backend checks each flashcard. The backend
   removes flashcards of low quality. The backend removes flashcards
   that repeat the same fact.

5. **Spaced repetition.** The backend uses the SM-2 algorithm. The SM-2
   algorithm decides when to show a flashcard again. The backend moves
   the flashcard further into the future when the user remembers it
   well. The backend moves the flashcard closer when the user does not
   remember it well.

6. **Search.** The backend lets the user search for a deck by name. The
   backend lets the user search for a flashcard inside a deck.

7. **Analytics.** The backend counts the flashcards a user studies each
   day. The backend calculates the percentage of correct answers.

### 3.2 Backend folder structure

| Folder or file | Content |
|---|---|
| `app/main.py` | The entry point of the backend. |
| `app/models.py` | The definition of the database tables. |
| `app/schemas.py` | The definition of the data sent to and from the frontend. |
| `app/routers/` | The code for each group of API endpoints. |
| `app/services/` | The code for PDF reading, card generation, and the SM-2 algorithm. |
| `tests/` | The automated tests for the backend. |

### 3.3 How to install the backend

Follow these steps to install the backend.

1. Open a terminal window.
2. Go to the `backend` folder.
3. Create a Python virtual environment. Type this command:
   ```bash
   python3 -m venv venv
   ```
4. Turn on the virtual environment. Type this command:
   ```bash
   source venv/bin/activate
   ```
5. Install the required Python packages. Type this command:
   ```bash
   pip install -r requirements.txt
   ```
6. Create a file named `.env` in the `backend` folder. Add these three
   values to the file:
   ```
   DATABASE_URL=<your database connection string>
   NVIDIA_API_KEY=<your NVIDIA API key>
   JWT_SECRET=<a long random string>
   ```
7. Start the backend server. Type this command:
   ```bash
   uvicorn app.main:app --reload
   ```
8. The backend now runs at `http://localhost:8000`.

### 3.4 How to test the backend

Follow these steps to run the automated tests.

1. Install the test packages. Type this command:
   ```bash
   pip install -r requirements-dev.txt
   ```
2. Run the tests. Type this command:
   ```bash
   pytest
   ```
3. Check the result. The terminal shows the number of tests that pass
   and the number of tests that fail.

---

## 4. The Frontend

The frontend uses the React library. The frontend uses the Vite build
tool. The frontend has bright colors and simple words. The bright colors
and simple words make the frontend easy for a child to use.

### 4.1 Main functions of the frontend

The frontend has these main functions:

1. **Login and register pages.** These pages let the user create an
   account and log in.

2. **Dashboard page.** This page shows all the decks that belong to the
   user. This page shows the study statistics for the current day. This
   page has a button to upload a new PDF file.

3. **Deck page.** This page shows the flashcards inside one deck. This
   page shows a progress chart. This page shows a chart of card
   categories. This page lets the user search inside the deck.

4. **Study page.** This page shows one flashcard at a time. The user
   taps the card to see the answer. The user rates how well the user
   remembered the answer. The frontend sends the rating to the backend.

### 4.2 Design of the frontend

The frontend design uses a mascot. The mascot is a fox named Pip. Pip
appears on many pages. Pip helps the user to feel welcome.

The frontend uses animation on many screens. The animation makes the
frontend feel alive. Examples of animation are a card that flips over,
and confetti that falls when the user finishes a study session.

The frontend adapts to the size of the screen. The frontend works on a
phone. The frontend works on a tablet. The frontend works on a desktop
computer.

### 4.3 Frontend folder structure

| Folder or file | Content |
|---|---|
| `src/App.jsx` | The routes of the application. |
| `src/pages/` | The code for each full page. |
| `src/components/` | The code for reusable parts, such as the flashcard and the mascot. |
| `src/context/AuthContext.jsx` | The code that manages the login state. |
| `src/lib/api.js` | The code that sends requests to the backend. |
| `tailwind.config.js` | The colors, fonts, and animation settings. |

### 4.4 How to install the frontend

Follow these steps to install the frontend.

1. Make sure the backend runs first. See section 3.3.
2. Open a new terminal window.
3. Go to the `frontend` folder.
4. Install the required packages. Type this command:
   ```bash
   npm install
   ```
5. Copy the example environment file. Type this command:
   ```bash
   cp .env.example .env
   ```
6. Open the `.env` file. Check that the value matches the backend
   address:
   ```
   VITE_API_URL=http://localhost:8000
   ```
7. Start the frontend server. Type this command:
   ```bash
   npm run dev
   ```
8. Open a web browser. Go to the address shown in the terminal. The
   address is usually `http://localhost:5173`.

### 4.5 How to build the frontend for production use

1. Go to the `frontend` folder.
2. Type this command:
   ```bash
   npm run build
   ```
3. The command creates a `dist` folder. The `dist` folder contains the
   files for a live website.

---

## 5. How to Use the Application

Follow these steps to use Cardventure.

1. Open the frontend address in a web browser.
2. Tap **Join the fun!** to create a new account. Enter an email
   address and a password.
3. Tap **New deck**.
4. Enter a title for the deck.
5. Select a PDF file, or drop the file into the upload area.
6. Tap **Let's go!**. The backend reads the file and creates the
   flashcards. This step can take up to one minute for a long PDF file.
7. Tap the new deck to open it.
8. Tap **Study now** to start a study session.
9. Tap a flashcard to see the answer.
10. Tap one of the four rating buttons. The buttons are **Oops!**,
    **Tricky**, **Got it!**, and **Easy!**.
11. Repeat steps 9 and 10 until all cards in the session are complete.

---

## 6. Maintenance Notes

- Check the backend log file for error messages after each deployment.
- Run the backend test suite before you deploy a new version. See
  section 3.4.
- Update the `tailwind.config.js` file to change the colors of the
  frontend. Do not change color values inside the component files.
- Update the `src/lib/taxonomy.js` file to change the labels of the
  card categories. Do not change the category keys. The category keys
  must match the backend.

---

## 7. Credits

Divansh built the frontend and the backend of Cardventure.

Made with 💛 by **Divansh**
