import sys
import os
import subprocess
import pandas as pd
import re
import numpy as np
from collections import defaultdict

#variable function declaration...........
np.random.seed(0)
d = 10
lamda = 0.1      # regularization constant
l = 0.001       # learning rate
beta = 20        # Social information weight  
	
Dict_Product_Category={}
No_of_items_in_category={}
TRAINING_MATRICES={}
Category_Circle = defaultdict(lambda : defaultdict(float))
Category_to_List_of_items={}

# user rating dict / dictionary(key-> userid, values-> dict(key->"ratings" etc, values->dictionary etc.))
user_rating_dict = {}
cat_list = ['Videos_&_DVDs','Books','Music','Video_Games','Toys','Online_Stores_&_Services','Software','Destinations','Cars','Kids_TV_Shows']
ofd=open("Sample_output_Equal_trust_5_fold","w")
cat_error_val = defaultdict(float)

def Trustee_List(Trustee):
    Trustee_set=set()
    for trustee in Trustee.split(","):
        Trustee_set.add(int(trustee))
    return Trustee_set

def Load_Dictionary(Product_df):
    for i in range(len(Product_df)):
        product_id=Product_df['Product_id'][i]
        Category_name=Product_df['Category_names'][i]
        Dict_Product_Category[product_id]=Category_name
        if Category_name not in No_of_items_in_category:
            No_of_items_in_category[Category_name]=0
        if Category_name not in Category_to_List_of_items:
            Category_to_List_of_items[Category_name]=list()
        No_of_items_in_category[Category_name]+=1
        Category_to_List_of_items[Category_name].append(product_id)


# Error derivative wrt Q
def Error_derivative_wrt_Q(I, R_Predicted,R, P,Q, S):
    First_term = np.matmul(np.multiply(I,(R_Predicted-R)), P)
    Second_term = lamda * Q
    Third_term = beta * np.subtract(Q, np.matmul(S,Q))
    fourth_term = beta *  np.matmul(S.transpose(),np.subtract(Q, np.matmul(S,Q))) 
    return First_term + Second_term + Third_term - fourth_term 

# Error derivative wrt P
def Error_derivative_wrt_P(I,R_Predicted,R,P,Q):
    First_term = np.matmul(np.multiply(I,(R_Predicted-R)).transpose(), Q)
    Second_term = lamda * P
    return First_term + Second_term 

# Training 
def Training(I,R_Predicted,R,P,Q,S):
    First_term = np.sum(np.sum(np.multiply(R - np.multiply(R_Predicted,I), R - np.multiply(R_Predicted,I)))) / (2.0)
    Second_term = (lamda/(2.0)) *(np.linalg.norm(Q,ord='fro') + np.linalg.norm(P,ord='fro'))
    Third_term_temp = np.subtract(Q, np.matmul(S,Q))
    Third_term = (beta/(2.0)) * pow((np.linalg.norm(Third_term_temp,ord='fro')),2)
    return First_term + Second_term + Third_term

print "------------------------ load files -------------------------"

# load files
# Products.csv -> Product_df
# User_Trust_Network.csv -> User_Trust_Network_df
# Rating.csv -> Training_df

Product_df = pd.read_csv("Products.csv") 
Load_Dictionary(Product_df)

User_Trust_Network_df = pd.read_csv("User_Trust_Network.csv", sep=':')  
User_Trust_Network_df['Trustee'] = map(Trustee_List,User_Trust_Network_df['Trustee'])

items=len(Product_df)

rating_df=pd.read_csv("Rating.csv")
List_Users=list(set(rating_df['User_id']))
users=len(List_Users)



print "---------------  initialize rating data structure ----------"
#initialize user_rating_dict
for userid in List_Users:
    user_rating_dict[userid] = {}
    user_rating_dict[userid]['ratings'] = {}

List_Category_row = []
for i in range(len(rating_df)):
    List_Category_row.append(Dict_Product_Category[rating_df['Product_id'][i]])
    userid = rating_df['User_id'][i]
    # default all as flase
    # flase -> training data
    # true  -> test data
    user_rating_dict[userid]['ratings'][i] = False

rating_df['Category'] = List_Category_row

# adding test range and test len 
for userid in List_Users:
    user_rating_dict[userid]['test_start'] = 0
    user_rating_dict[userid]['rating_len'] = len(user_rating_dict[userid]['ratings'])
    user_rating_dict[userid]['test_len'] = int(0.2 * user_rating_dict[userid]['rating_len'])
    user_rating_dict[userid]['test_end'] = user_rating_dict[userid]['test_len']
    for row_no,row in enumerate(user_rating_dict[userid]['ratings'].keys()):
        if row_no >= user_rating_dict[userid]['test_start'] and row_no <  user_rating_dict[userid]['test_end']:
            user_rating_dict[userid]['ratings'][row] = True
    
# adding test column to training_df
test_flag_row = []
for i in range(len(rating_df)):
    userid = rating_df['User_id'][i]
    test_flag_row.append(user_rating_dict[userid]['ratings'][i])

rating_df['test_flag'] = test_flag_row

#**************************************************************************************************
#***********************  5 fold cross validation starts ******************************************
#**************************************************************************************************

#update test & training data set
for loop_counter in range(1,6):
	for userid in List_Users:
	    user_rating_dict[userid]['test_start']  =  user_rating_dict[userid]['test_end']
	    user_rating_dict[userid]['test_end']   += user_rating_dict[userid]['test_len']
	    if user_rating_dict[userid]['test_end'] > user_rating_dict[userid]['rating_len']:
	        user_rating_dict[userid]['test_start'] = 0
	        user_rating_dict[userid]['test_end']   = user_rating_dict[userid]['test_len']

	    for row_no,row in enumerate(user_rating_dict[userid]['ratings'].keys()):
	        if row_no >= user_rating_dict[userid]['test_start'] and row_no <  user_rating_dict[userid]['test_end']:
	            user_rating_dict[userid]['ratings'][row] = True
	        else:
	            user_rating_dict[userid]['ratings'][row] = False

	for i in range(len(rating_df)):
	    userid = rating_df['User_id'][i]
	    rating_df.at[i,'test_flag'] = (user_rating_dict[userid]['ratings'][i])

	# creating test and training data structure
	Training_df = rating_df[ rating_df.test_flag == False ]
	Testing_df = rating_df[ rating_df.test_flag == True ]

	print "----------- create training matrices --------------------"

	with open("Category.txt") as Category_file:
	# with open("Ca.txt") as Category_file:
	    for Category in Category_file:
	        if Category.strip() not in cat_list:
	            continue
	        if Category.strip() in No_of_items_in_category:
	            #item matrix
	            P = np.random.randn(No_of_items_in_category[Category.strip()], d)
	            P = P.astype(dtype = np.float16)

	            #user matrix
	            Q = np.random.randn(users, d)
	            Q = Q.astype(dtype = np.float16)

	            #existing rating matrix users * items 
	            R = np.empty([users, No_of_items_in_category[Category.strip()]], dtype = np.float16)
	            R.fill(0.0)

	            #user trust matrix, users * users
	            S = np.empty([users,users], dtype = np.float16)
	            S.fill(0.0)

	            #bias matrix
	            r = np.empty([users,No_of_items_in_category[Category.strip()]], dtype = np.float16)       
	            r.fill(0.0)

	            I = np.empty([users, No_of_items_in_category[Category.strip()]], dtype = np.float16)
	            I.fill(0.0)

	            TRAINING_MATRICES[Category.strip()]=[P,Q,R,S,r,I]

	print "-------------- Initializing training matrices -----------------"

	# Filling matrix r
	Rating_count={}
	r_values={}
	for category,rating_group in Training_df.groupby('Category'):
	    if category not in cat_list:
	        continue
	    r_values[category]= np.mean(rating_group['Rating'])
	    Rating_count[category]=len(rating_group['Rating'])

	for category in r_values:
	    if category not in cat_list:
	        continue
	    r=TRAINING_MATRICES[category][4]
	    r.fill(r_values[category])
	    TRAINING_MATRICES[category][4]=r

	# Filling matrix R and I
	for user,item,category,rating in zip(Training_df['User_id'],Training_df['Product_id'],Training_df['Category'],Training_df['Rating']):
	    if category not in cat_list:
	        continue
	    if category in TRAINING_MATRICES:
	        R = TRAINING_MATRICES[category][2]
	        I = TRAINING_MATRICES[category][5]
	        row_index = List_Users.index(user)
	        col_index = Category_to_List_of_items[category].index(item)
	        R[row_index][col_index] = rating
	        I[row_index][col_index] = 1
	        TRAINING_MATRICES[category][2]=R
	        TRAINING_MATRICES[category][5]=I

	# Filling Matrix S as Category_Circle (Equal trust)
	for user, rating_group in Training_df.groupby('User_id'):
	    if user in List_Users:
	        for rating_entry in rating_group['Product_id']:
	                Category_Circle[Dict_Product_Category[rating_entry]][user] += 1

	# ****************** Equal Trust ***************************
	# Filling Matrix S as Category_Circle (Equal trust)

	for Category in Category_Circle.keys():
		if Category not in cat_list:
			continue
		category_user_list = set(Category_Circle[Category].keys())
		for i in range(users):
			user = User_Trust_Network_df['User_id'][i]
			if user in category_user_list:
				trustee = User_Trust_Network_df['Trustee'][i]
				Same_Category_trustee = trustee.intersection(category_user_list)
				S = TRAINING_MATRICES[Category][3]

				if len(Same_Category_trustee)!=0:
					val = 1.0 / float(len(Same_Category_trustee))
					for trustee_user in Same_Category_trustee:
						if user in List_Users:
							row_index = List_Users.index(user)
							col_index = List_Users.index(trustee_user)
							S[row_index][col_index] = val
					
					TRAINING_MATRICES[Category][3] = S

	# print "************* S matrix Created *******************"

	# for c in Category_Circle.keys():
	#     fname="./S_mat/S_matrix_for_"+str(c)
	#     fd=open(fname,"w")
	#     S=TRAINING_MATRICES[c][3] 
	#     for i in range(users):
	#       for j in range(users):
	#           fd.write(str(S[i][j])+" ")  
	#       fd.write("\n")  
	#     fd.close()

	print "---------------------------- Train --------------------------------------"

	Old_Error=1000
	for category in Category_Circle.keys():
	    if category not in cat_list:
	        continue
	    P=TRAINING_MATRICES[category][0]
	    Q=TRAINING_MATRICES[category][1]
	    R=TRAINING_MATRICES[category][2]
	    S=TRAINING_MATRICES[category][3]
	    r=TRAINING_MATRICES[category][4]
	    I=TRAINING_MATRICES[category][5]


	    R_Predicted = r + np.matmul(Q, P.transpose())   
	    # print "R_Predicted : ",R_Predicted.shape
	    ofd.write("################################"+"\n")
	    ofd.write(category+"\n")

	    iterations = 50  #change this

	    for itr in range(iterations): 

	        # print "iteration no : ", str(i+1)

	        error_der_P = Error_derivative_wrt_P(I,R_Predicted,R,P,Q)
	        error_der_Q = Error_derivative_wrt_Q(I,R_Predicted,R,P,Q,S)  

	        P = np.subtract(P, np.multiply(l, error_der_P))  
	        # for i in range(No_of_items_in_category[category]):
	        #     for j in range(d):
	        #         P[i][j] -= (l * error_der_P[i][j])

	        Q = np.subtract(Q, np.multiply(l, error_der_Q))

	        R_Predicted = r + np.matmul(Q, P.transpose())

	        RMSE_train = np.sqrt(np.sum(np.square(np.subtract(np.multiply(I,R_Predicted),R)))/float(Rating_count[category]))

	        New_Error = Training(I,R_Predicted,R,P,Q,S)

	        print "iteration no : ",str(itr),": Test round: ",loop_counter," ,", category,' RMSE_train : ', str(RMSE_train)
	        # print "P[0]: ", P[0]
	        # print "Q[0]: ", Q[0]
	        ofd.write("iteration : "+str(itr)+" # Test round : "+str(loop_counter)+" # RMSE_train : "+str(RMSE_train)+"\n")

	        if itr>0:    
	            if ((Old_Error-New_Error)<10):
	                break    
	        Old_Error = New_Error
	    	
	    	TRAINING_MATRICES[category][0]=P
	    	TRAINING_MATRICES[category][1]=Q
	        
	# ----------------------------------- Test ----------------------------------------
	ofd.write("############################################################################"+"\n")
	ofd.write("####################### Testing Results ######################################"+"\n")
	for category,rating_group in Testing_df.groupby('Category'):
	    if category not in cat_list:
	        continue
	    if len(rating_group) == 0:
	        continue
	    if category in TRAINING_MATRICES:
	        P=TRAINING_MATRICES[category][0]
	        Q=TRAINING_MATRICES[category][1]
	        R=TRAINING_MATRICES[category][2]
	        S=TRAINING_MATRICES[category][3]
	        r=TRAINING_MATRICES[category][4]
	        I=TRAINING_MATRICES[category][5]

	        R_Test=np.empty(R.shape, dtype = np.float16)
	        I_Test=np.empty(R.shape, dtype = np.float16)
	        R_Test.fill(0.0)
	        I_Test.fill(0.0)
	        for user,item,rating in zip(rating_group['User_id'],rating_group['Product_id'],rating_group['Rating']):
	            row_index=List_Users.index(user)
	            col_index=Category_to_List_of_items[category].index(item)
	            R_Test[row_index][col_index]=rating
	            I_Test[row_index][col_index]=1

	        R_Predicted = r + np.matmul(Q, P.transpose())

	        RMSE_test = np.sqrt(np.sum(np.square(np.subtract(np.multiply(I_Test,R_Predicted),R_Test)))/float(len(rating_group)))
	        #print I_Test #,R_Predicted)
	        #print np.sum(np.square(np.subtract(np.multiply(I_Test,R_Predicted),R_Test)))
	        print category, '  RMSE_test : ', str(RMSE_test)
	        ofd.write(category+" # RMSE_test : "+str(RMSE_test)+"\n")
	        cat_error_val[category] += RMSE_test

	ofd.write("############################################################################"+"\n")
print "\n\n====================== final average accuracy over 5 fold cross validation ============================\n"
ofd.write("############################################################################"+"\n")
ofd.write("\n\n================= final average accuracy over 5 fold cross validation ===============\n")
for cat in cat_error_val.keys():
    # print cat," error:", cat_error_val[cat]/2.0
    x=cat_error_val[cat]/5.0
    print cat," error:", str(x)
    ofd.write(cat+" Error : "+str(x)+"\n")

ofd.close()