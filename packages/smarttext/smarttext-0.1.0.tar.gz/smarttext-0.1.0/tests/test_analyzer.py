from smarttext.analyzer import word_count, sentence_count, avg_word_length

def test_word_count():
    assert word_count("Hello world!") == 2

def test_sentence_count():
    assert sentence_count("Hi! How are you?") == 2

def test_avg_word_length():
    assert avg_word_length("abc def") == 3
