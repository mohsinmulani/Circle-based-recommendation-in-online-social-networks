# Circle-based-recommendation-in-online-social-networks

Reimplementation of paper published : http://eeweb.poly.edu/faculty/yongliu/docs/CircleRec.pdf

Executing code - 

Step 1 - 
Download dataset from “http://alchemy.cs.washington.edu/data/epinions/” 
Extract ./epinions/epinions/ directory 

Step 2 - 
Go to path ./epinions/epinions/ 

Step 3 - 	
Execute build_files.py after setting user_lower_limit & user_upper_limit variables in 
the file (default setting 0-1000 users), it will generate files Products.csv, 
Rating.csv, User_Trust_Network.csv, Category.txt. 

Step 4 - 
Execute Equal_trust.py to get result for Equal trust
Execute Varient_a.py for Expertise based trust varient_a
Execute Varient_b.py for Expertise based trust varient_b
Execute trust_spliting.py for Trust Spliting
  

