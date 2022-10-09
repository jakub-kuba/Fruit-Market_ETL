The program takes fruit prices from the website:
https://khrybitwy.pl/notowania_cenowe/ceny-owocow-i-warzyw.html

The data is sent to the database and to the file.

The table 'fruit' in the database looks like this:

 #   Column         Non-Null Count  Dtype         
---  ------         --------------  -----         
 0   Date           0 non-null      datetime64[ns]
 1   Name           0 non-null      object        
 2   Avarage_Price  0 non-null      float64
 
The script is executed daily and the current CSV file can be found here:
https://data.jakub-kuba.com/market
