const express = require("express");
const mysql = require('mysql');
const app = express();

var db = mysql.createConnection({
  host: '127.0.0.1',
  user: 'root',
  password: 'inventorypw',
  database: 'inventory'
});

db.connect(function(error) {
  if (error) throw error;
  console.log('Database Connected.');
});

app.get('/v1/inventory', (request, response) => {
    db.query('SELECT * from inventory', (error, rows) => {
        if(error) throw error;
        db.end();
        console.log('=== rows ===', rows);
        response.send(rows);
    });
});

app.get('/v1/inventory_history', (request, response) => {
    db.query('SELECT * from inventory_history', (error, rows) => {
        if(error) throw error;
        db.end();
        console.log('=== rows ===', rows);
        response.send(rows);
    });
});


app.listen(8090, () => {
    console.log('8090 port listening...');
});
