import streamlit as st
import sqlite3
import uuid
from datetime import datetime
from src.Agent.chat import chat_service

# ---------------------------------------------------------------------------
# SQLite — lightweight local store for conversation history (not product data)
# ---------------------------------------------------------------------------

def init_db():
    conn = sqlite3.connect("chat_history.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            created_at DATETIME,
            last_seen DATETIME,
            display_name TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME,
            user_id TEXT,
            description TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER,
            role TEXT,
            content TEXT,
            timestamp DATETIME,
            FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
        )
    """)
    conn.commit()
    return conn


def get_user_id():
    if "user_id" not in st.session_state:
        st.session_state["user_id"] = str(uuid.uuid4())
    return st.session_state["user_id"]


def load_chat_history(conn, user_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            cs.id,
            cs.timestamp,
            cs.user_id,
            (SELECT m.content FROM messages m
             WHERE m.session_id = cs.id ORDER BY m.timestamp ASC LIMIT 1)  AS first_message,
            (SELECT m.content FROM messages m
             WHERE m.session_id = cs.id ORDER BY m.timestamp DESC LIMIT 1) AS last_message
        FROM chat_sessions cs
        WHERE cs.user_id = ?
        ORDER BY cs.timestamp DESC
        LIMIT 5
    """, (user_id,))
    return cursor.fetchall()


def load_chat_session(conn, session_id):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, timestamp
        FROM messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
    """, (session_id,))
    return cursor.fetchall()


# ---------------------------------------------------------------------------
# Session state defaults
# ---------------------------------------------------------------------------

if "messages" not in st.session_state:
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi! I'm the King Arthur Baking assistant. How can I help you today?"}
    ]
conn = init_db()
user_id = get_user_id()

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

if st.sidebar.button("Clear History"):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM messages WHERE session_id IN (SELECT id FROM chat_sessions WHERE user_id = ?)", (user_id,))
    cursor.execute("DELETE FROM chat_sessions WHERE user_id = ?", (user_id,))
    conn.commit()
    st.session_state["messages"] = [
        {"role": "assistant", "content": "Hi! I'm the King Arthur Baking assistant. How can I help you today?"}
    ]
    st.success("Chat history cleared.")

chat_history = load_chat_history(conn, user_id)

with st.sidebar.expander("Previous Chats"):
    if chat_history:
        for i, row in enumerate(chat_history):
            session_id, timestamp, _, first_message, _ = row
            label = (first_message[:40] + "...") if first_message and len(first_message) > 40 else (first_message or f"Session {i + 1}")
            if st.button(label, key=f"session_{session_id}"):
                loaded = load_chat_session(conn, session_id)
                st.session_state["messages"] = [
                    {"role": msg[0], "content": msg[1]} for msg in loaded
                ]
    else:
        st.write("No chat history available.")

# ---------------------------------------------------------------------------
# Main chat area
# ---------------------------------------------------------------------------

st.title("King Arthur Baking - AI Assistant")

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input("Ask me anything about King Arthur Baking products..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    with st.spinner("Searching products..."):
        result = chat_service.process_message(prompt, st.session_state.messages[:-1])

    st.session_state.messages.append({"role": "assistant", "content": result["response"]})
    st.chat_message("assistant").write(result["response"])

    # Persist to SQLite
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO users (id, created_at, last_seen, display_name)
        VALUES (?, COALESCE((SELECT created_at FROM users WHERE id = ?), ?), ?, 
                COALESCE((SELECT display_name FROM users WHERE id = ?), NULL))
    """, (user_id, user_id, datetime.now(), datetime.now(), user_id))

    cursor.execute("""
        INSERT INTO chat_sessions (timestamp, user_id, description)
        VALUES (?, ?, ?)
    """, (datetime.now(), user_id, prompt))
    session_id = cursor.lastrowid

    for msg in st.session_state.messages[-2:]:
        cursor.execute("""
            INSERT INTO messages (session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?)
        """, (session_id, msg["role"], msg["content"], datetime.now()))
    conn.commit()

conn.close()
