Lucian Murphy
lucian@uoregon.edu

What it does 

You enter the control distances in either KM or MI, then the open and close times fill in automatically. Then you can press submit to save it to the DB and view it by hitting display.

speed table
| Segment (km) | Min speed (close) | Max speed (open) |
|--------------|-------------------|------------------|
| 0–200 -------| 15 ---------------| 34---------------|
| 200–400 -----| 15 ---------------| 32 --------------|
| 400–600 -----| 15 ---------------| 30 --------------|
| 600–1000 ----| 11.428 -----------| 28 --------------|
| 1000–1300 ---| 13.333 -----------| 26---------------|

rules
- open time is the sum of distance and its max speed, close is the same 
but with min speed and it is rounded to the nearest minute
- finish time is closed: 200 = 13:20, 300 = 20:00, 400 = 27:00,
600 = 40:00, 1000 = 75:00
- control past the finish is timed as finish, but beyond 20% it is an error 
- Valid brevets here are 200, 300, 400, 600, 1000. All in Kilometers

Running Program

`cd (path to the proj6-rest folder) copy\DockerRestAPI`, 
`docker compose up --build`, then go to http://localhost:5000 
for the website, https://localhost:5001/listAll for the list, 
and https://localhost:5002 for the website that shows the db
in a table

To run tests
 `docker compose run --rm brevets nosetests --exe`, it wasnt working otherwise