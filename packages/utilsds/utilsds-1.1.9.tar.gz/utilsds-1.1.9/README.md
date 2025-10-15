# utils

Rozwiązanie zawierające klasy i funkcje wykorzystywane podczas projektów.
Struktura repozytorium stworzono tak, aby udostępnić ją jako [utilsds](https://pypi.org/project/utilsds/).

Biblioteka została stworzona na podstawie [tej instrukcji](https://www.turing.com/kb/how-to-create-pypi-packages).

Aby zaktualizować klasy/funkcje pierwsze na stronie https://pypi.org/ należy:
- stworzyć konto
- dodać 2FA z wykorzystaniem aplikacji Google Authenticator
- stworzyć plik home/.pypirc (najlepiej zarządzać tym plikiem z poziomu konsoli, ponieważ pozostaje on ukryty)
- wygenerować w ustawieniach `API tokens` a następnie wkleić wygenerowany kod do wcześniej stworzonego pliku .pypirc (zgodnie z instrukacjami podanymi w ustawieniach).
- wprowadzić aktualizacje
- dokonać modyfikacji w pliku setup.py (szczególnie zwrócić uwagę na inkrementację numeracji wersji)
- jeżeli jest potrzebne, zainstalować `pip install --upgrade setuptools wheel twine`
- wykonać komendę `python setup.py sdist bdist_wheel`
- wykonać komendę `twine upload --skip-existing dist/*`
- spushować zmiany na gitlaba
