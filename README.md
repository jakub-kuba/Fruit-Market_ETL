The program takes fruit prices from the website:
https://khrybitwy.pl/notowania_cenowe/ceny-owocow-i-warzyw.html

The data is sent to the database and to the file.

The table 'fruit' in the 'market' database has 3 columns:

1. Date (datetime64[ns])
2. Name (object)      
3. Avarage_Price (float64)
 
The script is executed daily and the current CSV file can be found here:
https://data.jakub-kuba.com/market
