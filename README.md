This model is focused on the best supplier EACH order INDEPENDENT to the rest. 
Risk occur very much when one set up an equally ranked Supplier array (cost lead time and delay probability).
The total amount of units rewarded to the i-th supplier may easily break-up the maximum capacity.   
Don't miss the meaning of "delay probability" - at any run the code produce the prrbaility value and
uses it to produce the expected delay - i.e. think of it not a performance simulator.
Use it as it is i.e. someone else's department bayesian evaluation of the next performance. 
The score function is penalità = w_LT * LT_eff + w_C * Costo_totale that ON PURPOSE is very raw and can therefore be surpringly
inconsistent when costs are very numerical different to delay- lead time units.
