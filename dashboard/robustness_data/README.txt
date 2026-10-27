Static inputs for the Robustness page. Copied unchanged from the thesis-revision review
(review/ folder of the project); the dashboard reads them and never recomputes them.

sensitivity_summary.csv      9 profiles x 5 sizes: weighted pick and the picks under share-of-total,
                             session B, scalability removed, rank sum and runtime only (session A data
                             unless stated; session B and scalability removal computed offline from the
                             stored runs).
consequence_2a_forward.csv   Fast SNN: the N = 100 choice reused at each size (runtime ratio to the best).
consequence_2a_reverse.csv   Fast SNN: the N = 10,000 choice reused at each size.
consequence_2b_session.csv   Cells whose choice differs between sessions: both backends on session-B data.
