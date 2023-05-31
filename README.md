# Cryptocurrencies - Django Project

This is a simple Django web application that provides up-to-date cryptocurrency rates and a currency converter. The application fetches cryptocurrency data from the CoinGecko API, and also includes functionalities for caching and asynchronously fetching data to improve performance.

![image](https://github.com/roberts911/Cryptocurrencies/assets/85109223/16eeccb8-e23a-47b4-a390-1b5147af32e1)


## Features

1. **Cryptocurrency List:** The application fetches a list of cryptocurrencies along with their current prices in PLN. 

2. **Currency Converter:** Allows conversion of a given amount of a selected cryptocurrency to PLN.

![image](https://github.com/roberts911/Cryptocurrencies/assets/85109223/44827856-40b0-4e97-86a5-ee9761ea327d)


3. **Cryptocurrency Chart:** Displays a chart of a selected cryptocurrency's price over a selected number of days.

![image](https://github.com/roberts911/Cryptocurrencies/assets/85109223/58df0dc3-ab29-4c6c-8870-54899fab3f0f)


## Tech Stack

1. **Back-end:** Django framework.

2. **Front-end:** HTML, CSS, Plotly for data visualization.

3. **API:** CoinGecko API.

4. **Libraries:** PyCoinGecko, Plotly, httpx, Django's built-in caching framework.

## Instruction

1. Clone the repository to your local machine.

     ```
    git clone git@github.com:roberts911/Cryptocurrencies.git
    ```

2. Install the required packages using pip:

    ```
    pip install django httpx plotly pycoingecko
    ```

3. Start the Django server:

    ```
    python manage.py runserver
    ```

4. Open a web browser and navigate to `localhost:8000` to access the application.

## Author

Robert Siurek
