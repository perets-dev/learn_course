# Обзор библиотек numpy, pandas

## Инструкция
1. Создайте папку data и поместите туда файл [GOOG.csv](https://www.kaggle.com/datasets/adarshraj321/googcsv?resource=download) и файл [credit_risk_dataset.csv](https://www.kaggle.com/datasets/laotse/credit-risk-dataset/data)
2. Создайте окружение Python - `conda create -n "week_2" python=3.9`
3. Активируйте окружение Python - `conda activate week_2`
4. установите библиотеки из requirements.txt - `pip install -r requirements.txt`


## Описание данных (credit_risk_dataset.csv)

| Название признака | Описание |
|--------------|-------------|
| person_age | Возраст |
| person_income | Годовой доход |
| person_home_ownership | Владение жильем |
| person_emp_length | Стаж работы (в годах) |
| loan_intent | Цель кредита |
| loan_grade | Кредитная категория |
| loan_amnt | Сумма кредита |
| loan_int_rate | Процентная ставка |
| loan_status | Статус кредита (0 - отсутствие просрочки, 1 - просрочка) |
| loan_percent_income | Процент дохода |
| cb_person_default_on_file | Историческая просрочка |
| cb_preson_cred_hist_length | Стаж кредитной истории |