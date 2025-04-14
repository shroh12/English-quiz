def show_quiz(difficulty="medium"):
    zipped = zip(
        range(len(st.session_state["quiz"])),
        st.session_state["quiz"],
        st.session_state["answ"],
        st.session_state["audio"],
        st.session_state["choices"],
    )

    for idx, quiz, answ, audio, choices in zipped:
        key_feedback = f"feedback_{idx}"
        init_session({key_feedback: ""})

        with st.form(f"form_question_{idx}", border=True):
            st.markdown("""
            <div style="background-color:#e6f4ea; padding:10px; border-radius:10px; text-align: center;">
                <h4 style="color:#006d2c; margin: 0;">문제</h4>
            </div>
            """, unsafe_allow_html=True)

            st.audio(audio)

            quiz_display = quiz.replace("**", "").replace(
                "_____", "<span style='color:red; font-weight:bold;'>_____</span>"
            )
            st.markdown(f"<p style='font-size:17px;'>{quiz_display}</p>", unsafe_allow_html=True)

            # 빈칸 개수 파악
            is_multi_blank = all(isinstance(c, list) for c in choices)
            user_choices = []

            if not choices:
                st.error("선택지가 없습니다. 다시 문제를 생성하세요.")
                continue

            if is_multi_blank:
                for i, choice_set in enumerate(choices):
                    key_choice = f"choice_{idx}_{i}"
                    init_session({key_choice: ""})
                    user_choice = st.radio(
                        f"빈칸 {i + 1} 보기 👇",
                        choice_set,
                        key=key_choice
                    )
                    user_choices.append(user_choice)
            else:
                key_choice = f"choice_{idx}_0"
                init_session({key_choice: ""})
                if st.session_state[key_choice] not in choices:
                    st.session_state[key_choice] = choices[0]
                user_choice = st.radio(
                    "보기 중 하나를 선택하세요👇",
                    choices,
                    key=key_choice
                )
                user_choices.append(user_choice)

            submitted = st.form_submit_button("정답 제출 ✅", use_container_width=True)

            if submitted:
                with st.spinner("채점 중입니다..."):
                    is_correct = user_choices == answ

                    if is_correct:
                        feedback = "✅ 정답입니다! 🎉"
                    else:
                        # 각 빈칸별 피드백 생성
                        feedback_parts = []
                        for u, a in zip(user_choices, answ):
                            feedback_parts.append(generate_feedback(u, a))
                        feedback = f"❌ 오답입니다.\n\n" + "\n\n".join(feedback_parts)

                    if "quiz_data" not in st.session_state:
                        st.session_state["quiz_data"] = []

                    st.session_state["quiz_data"].append({
                        "question": quiz_display,
                        "correct": is_correct,
                        "difficulty": difficulty
                    })

                    st.session_state[key_feedback] = feedback

        # 해설 출력
        feedback = st.session_state.get(key_feedback, "")
        if feedback:
            with st.expander("📚 해설 보기", expanded=True):
                st.markdown(f"**정답:** {', '.join(answ)}")
                st.markdown(feedback, unsafe_allow_html=True)
