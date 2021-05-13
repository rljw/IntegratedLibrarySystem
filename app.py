from flask import Flask, g, render_template, url_for, redirect, request, session, flash
from sqlalchemy import create_engine
from datetime import datetime
from pymongo import MongoClient, TEXT
from datetime import date

engine = create_engine('mysql+pymysql://root:0000@localhost:3306/library?charset=utf8')
connection = engine.connect()

app = Flask(__name__)
app.secret_key = 'hello'  # to make sessions work
client = MongoClient("mongodb://127.0.0.1:27017")
db = client["library"]
collection = db["libbooks"]


@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET','POST']) #initial landing page of ILS
def login():
    if request.method == 'POST':
        book_user_query = "SELECT borrow_userID FROM book WHERE DATEDIFF(DueDate, (CURDATE())) < 0"
        response = connection.execute(book_user_query)
        users = response.fetchall()
        print(users)
        for user_id in users:
            query = "UPDATE book SET ReserveStatus = 0, reserve_userID = null, ReservationDate = null WHERE reserve_userID = %s"
            response = connection.execute(query, user_id)
        userID = request.form["userID"]
        password=request.form['password']
        if userID == "admin" and password == "admin": #admin login
            return redirect(url_for("adminhome"))

        else:
            #query from MYSQL
            query = 'SELECT * FROM user WHERE userID="{}"'.format(userID)
            print(query)
            usernamedata = connection.execute(query)
            nonexistent = str(usernamedata.fetchone())
            print(usernamedata.fetchone())
            querypwd = 'SELECT password FROM user WHERE userID="{}"'.format(userID)
            passworddata = connection.execute(querypwd)
            correctpwd = passworddata.fetchone()
            pwdexist = str(usernamedata.fetchone())
            if nonexistent != "None": #if user exists
                if correctpwd[0] == password: #and password is correct
                    session['user_id'] = userID
                    return redirect(url_for("profile", un=userID))
                else: #password not correct
                    flash("Wrong password. Please try again")
                    return redirect(url_for("login"))
            else:
                #userID does not exist
                flash("Incorrect or non-existent userID. Please register an account or try again")
                return redirect(url_for("login"))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['userName']
        userID = request.form['userID']
        password = request.form['password']
        email = request.form['Email']
        phonenumber = request.form["phoneNumber"]
        if len(userID)>4:
            flash("Please use userID with only 4 characters")
            return redirect(url_for("register"))
        elif len(phonenumber) > 8 : #if phone number > 8 or not all are numbers
            flash("Your phone number should only consist of integers and is no more  than 8 characters long")
            return redirect(url_for("register"))
        else:
            query = 'SELECT * FROM user WHERE userID="{}"'.format(userID)
            checkaccount = connection.execute(query)
            account = checkaccount.fetchall()
            print(account)
            if account:
                flash("Account already exists! Use another unique userID")
                return render_template('register.html')
            else:
                connection.execute(
                    'INSERT INTO user VALUES("{}", "{}", "{}", "{}", "{}")'.format(userID, username, password, email,
                                                                                   phonenumber))
                connection.execute('INSERT INTO fine VALUES("{}", 0)'.format(userID))
                flash("You have successfully registered! Please login")
    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    return render_template("profile.html")


@app.route('/adminhome', methods=["GET", "POST"])
def adminhome():
    return render_template("adminhome.html")


@app.route('/allborrows', methods=["GET", "POST"])
def allborrows():
    # if we want to display who borrowed the book, then use:
    query = "SELECT bookID, book.ISBN, title, categories, shortDesc, authors,borrow_userID from Book left join BookAttributes on Book.ISBN = BookAttributes.ISBN where book.BorrowStatus = 1"
    allborrowing = connection.execute(query)
    data = allborrowing.fetchall()
    return render_template("allborrows.html", borrowing=data)


@app.route('/allreserves', methods=["GET", "POST"])
def allreserves():
    # if we want to display who reserved the book, then use:
    query = "SELECT bookID, book.ISBN, title, categories, shortDesc, authors, reserve_userID from Book left join BookAttributes on Book.ISBN = BookAttributes.ISBN where book.ReserveStatus = 1"
    allreserve = connection.execute(query)
    data = allreserve.fetchall()
    return render_template("allreserves.html", reserving=data)


@app.route('/unpaidfines', methods=["GET", "POST"])
def unpaidfines():
    query = "SELECT DISTINCT(user.userID), userName, email, phoneNumber, fine.amount + SUM(IFNULL(DATEDIFF(DueDate, (CURDATE()))*(-1), 0)) AS Fine \
            FROM (user LEFT JOIN fine ON user.userID = fine.userID) \
		    LEFT JOIN book ON user.userID = book.borrow_userID \
            WHERE user.userID IN (SELECT DISTINCT(userID) \
			                        FROM fine \
			                        WHERE amount>0) OR \
 	        user.userID IN (SELECT DISTINCT(borrow_userID)\
				            FROM book\
				            WHERE DATEDIFF(DueDate, (CURDATE())) < 0)\
            GROUP BY user.userID"
    print(query)
    unpaidfine = connection.execute(query)
    data = unpaidfine.fetchall()
    print(data)
    return render_template("unpaidfines.html",fines=data)


@app.route('/logout')
def logout():
    return redirect(url_for("login"))


@app.route("/userreserve", methods=["GET", "POST"])
def userreserve(pm=None):
    # pm: for flash parameters
    user = session['user_id']
    print(user)
    query = 'SELECT bookID, title, ReservationDate, DATE_ADD(DueDate, INTERVAL 1 DAY) as AvailableDate, BorrowStatus FROM book LEFT JOIN BookAttributes on book.ISBN = BookAttributes.ISBN where reserve_userID = "{}"'.format(
        user)
    print(query)
    userborrow = connection.execute(query)
    data = userborrow.fetchall()
    print(data)
    if pm == 1:
        # print('flash')
        flash("Your reservation has been cancelled.")
    if pm == 2:
        flash("Your book has been borrowed.")
    if pm == 3:
        flash("Maximum number of books borrowed already.")
    if pm == 4:
        flash("Sorry, you cannot borrow the book yet.")
    if pm == 5:
        flash("Please pay any outstanding fines before borrowing")
    if pm == 6:
        flash("Seems like you have a book overdue! Return the book before borrowing")

    return render_template("userreserve.html", userreserve=data)


@app.route("/borrowfromreserve<book>", methods=["POST", "GET"])
def borrowfromreserve(book):
    user = session['user_id']
    UserID = user
    BookID = book
    query1 = "SELECT * FROM book WHERE bookID = %s AND BorrowStatus = 0"
    response1 = connection.execute(query1, BookID)
    if (str(response1.fetchone()) != "None"):
        query4 = "SELECT COUNT(bookID) AS NumBooksBorrowed FROM book WHERE borrow_userID = %s"
        response4 = connection.execute(query4, UserID)
        check = response4.fetchall()

        query5 = "SELECT amount FROM fine WHERE userID = %s"
        response5 = connection.execute(query5, UserID)

        query6 = "SELECT *, DATEDIFF(DueDate, (CURDATE())) AS DaysRemaining FROM book WHERE borrow_userID = %s HAVING DaysRemaining < 0"
        response6 = connection.execute(query6, UserID)

        if (check[0][0] >= 4):
            return userreserve(3)

        elif (str(response5.fetchone()) != '(0,)'):
            return userreserve(5)

        elif (len(response6.fetchall()) > 0):
            return userreserve(6)

        else:
            query = "UPDATE book SET ReserveStatus = 0, reserve_userID = null, ReservationDate = null WHERE bookID = {} AND reserve_userID = \"{}\"".format(
                book, user)
            response = connection.execute(query)
            query2 = "UPDATE book SET BorrowStatus = 1, borrow_userID = %s ,BorrowDate = CURDATE(), DueDate = DATE_ADD(CURDATE(), INTERVAL 28 DAY) WHERE bookID = %s"  # UserID and BookID to be entered by the user
            execute2 = connection.execute(query2, UserID, BookID)
            return userreserve(2)
    else:
        return userreserve(4)


@app.route("/cancel<book>", methods=["POST", "GET"])
def cancel_reservation(book):
    user = session['user_id']
    query = "UPDATE book SET ReserveStatus = 0, reserve_userID = null, ReservationDate = null WHERE bookID = {} AND reserve_userID = \"{}\"".format(
        book, user)
    response = connection.execute(query)
    print("Your reservation has been cancelled")
    return userreserve(1)

@app.route("/userborrow", methods=["GET", "POST"])
def userborrow(pm=None):  # i must find a way to retrieve userID
    # pm: for flash parameters
    user = session['user_id']
    print(user)
    query = 'SELECT bookID, title, BorrowDate, DueDate, Extend FROM book LEFT JOIN BookAttributes on book.ISBN = BookAttributes.ISBN where borrow_userID = "{}"'.format(
        user)
    print(query)
    userborrow = connection.execute(query)
    data = userborrow.fetchall()
    print(data)
    if pm == 1:
        # print('flash')
        flash("Sorry, extension failed! You have exceeded your extension limit. Please return the book on time.")
    elif pm == 2:
        flash("Sorry someone else has already reserved the book. You cannot extend.")
    elif pm == 3:
        flash("Extension succeeds. Thank you for extending your borrow.")
    elif pm == 4:
        flash("Thank you! Your book has been returned.")
    elif pm == 5:
        flash("Sorry your book is overdue. You cannot extend.")
    return render_template("userborrow.html", userborrow=data)


@app.route("/extend<book>", methods=["GET", "POST"])
def extend(book):
    query1 = "SELECT Extend FROM book WHERE bookID = {}".format(book)
    execute1 = connection.execute(query1)

    query2 = "SELECT reserve_userID FROM book WHERE bookID = {}".format(book)
    execute2 = connection.execute(query2)

    query3 = "SELECT DATEDIFF(DueDate, (CURDATE())) AS DaysRemaining FROM book WHERE bookID = {}".format(book)
    execute3 = connection.execute(query3)

    check1 = execute1.fetchall()
    check2 = execute2.fetchall()
    check3 = execute3.fetchall()

    print(check1)
    print(check2)
    if (check1[0][0] == 1):
        print("Sorry you have exceeded your extension limit")
        return userborrow(1)
    elif (check2[0][0]):
        print("Sorry someone else has already reserved the book. You cannot extend.")
        return userborrow(2)
    elif (check3[0][0] < 0):
        print("Sorry your book is overdue. You cannot extend.")
        return userborrow(5)
    else:
        query3 = "UPDATE book SET DueDate = DATE_ADD(DueDate, INTERVAL 28 DAY), Extend = 1 WHERE bookID = {} AND ReserveStatus = 0".format(
            book)
        execute3 = connection.execute(query3)
        print("Thank you for extending your borrow")
        return userborrow(3)


@app.route('/return<book>', methods=['POST', 'GET'])
def return_book(book):
    user = session['user_id']
    DueDate = "SELECT book.DueDate FROM book WHERE book.bookID = {}".format(book)
    response1 = connection.execute(DueDate)
    x = response1.fetchall()
    currDate = datetime.now().date()
    print(x[0][0])
    print(currDate)
    fine = (x[0][0] - currDate)
    z = int(fine.days)
    print(z)

    if (fine.days < 0):
        query4 = "UPDATE book SET borrow_userID = null, BorrowStatus = 0, BorrowDate = null, ReturnDate = null, Extend=0,DueDate = null WHERE bookID = {}".format(
            book)
        execute4 = connection.execute(query4)
        query2 = "UPDATE fine SET amount =  amount + {} WHERE userID = \"{}\"".format(-z, user)
        response2 = connection.execute(query2)
        print("You have incurred a fine of $" + str(
            response2) + " due to late return. Kindly pay the fine before borrowing/reserving your next book")
        # here return a now template with a fine and a link to go to the fine view / page
        return render_template('userborrowreturnfine.html')

    query3 = "UPDATE book SET borrow_userID = null, BorrowStatus = 0, BorrowDate = null, ReturnDate = null, Extend = 0, DueDate = null WHERE bookID = {}".format(
        book)
    execute3 = connection.execute(query3)
    print("Your book has been returned.")
    return userborrow(4)


@app.route("/search", methods=["GET", "POST"])
def search():
    return render_template("search.html")

def simplesearch():
    simple = request.form["title"]
    if simple:
        collection.drop_indexes()
        collection.create_index([('title', TEXT)], default_language='english')
        r1 = collection.find({"$text": {"$search": simple}})
        result = []
        for ob in r1:
            query1 = "SELECT * FROM book WHERE bookID = %s AND BorrowStatus = 0 AND ReserveStatus = 0"
            query2 = "SELECT DUEDATE FROM Book where BookID = %s"
            response1 = connection.execute(query1, ob['_id'])
            response2 = connection.execute(query2, ob['_id'])
            duedate = response2.fetchone()
            print(duedate)
            if response1.fetchone() is None and duedate is not None:  # if borrowed
                ob['availability'] = "No"
                ob['duedate'] = str(duedate[0])
            elif response1.fetchone() is None and duedate is None:  # does not exist
                ob['availability'] = "No"
                ob['duedate'] = "NIL"
            else:
                ob['availability'] = "Yes"
                ob['duedate'] = "NIL"
        if result:
            return render_template('result.html', result=result)
        else:
            flash("No book found. Did you misspell the keywords?")
            # return "No book found. Did you misspell the keywords?", 400
            return redirect('/search')
    else:
        flash("Invalid input, please re-enter!")
        return redirect('/search')



@app.route('/adsearch', methods=['GET', 'POST'])
def form():
    return render_template('adsearch.html')


@app.route('/results', methods=['POST'])
def advancedsearch():
    title = request.form.get('title')
    author = request.form.get('author')
    category = request.form.get('category')
    publishedDate = request.form.get('publishedDate')
    result1 = []
    result2 = []
    result3 = []
    result4 = []
    result = []
    if title or author or category or publishedDate:

        if title:
            collection.drop_indexes()
            collection.create_index([('title', TEXT)], default_language='english')
            r1 = collection.find({"$text": {"$search": title}})
            for ob in r1:

                query1 = "SELECT * FROM book WHERE bookID = %s AND BorrowStatus = 0 AND ReserveStatus = 0"
                query2 = "SELECT DUEDATE FROM book where bookID = %s"
                response1 = connection.execute(query1, ob['_id'])
                response2 = connection.execute(query2, ob['_id'])
                duedate = response2.fetchone()
                print(duedate)
                if response1.fetchone() is None and duedate is not None: #if borrowed
                    ob['availability'] = "No"
                    ob['duedate'] = str(duedate[0])
                elif response1.fetchone() is None and duedate is  None: #does not exist
                    ob['availability'] = "No"
                    ob['duedate'] = "NIL"
                else:
                    ob['availability'] = "Yes"
                    ob['duedate'] = "NIL"
                result1.append(ob)
            result = result1

        if author:
            collection.drop_indexes()
            collection.create_index([('authors', TEXT)], default_language='english')
            r2 = collection.find({"$text": {"$search": author}})
            for ob in r2:
                query1 = "SELECT * FROM book WHERE bookID = %s AND BorrowStatus = 0 AND ReserveStatus = 0"
                query2 = "SELECT DUEDATE FROM Book where BookID = %s"
                response1 = connection.execute(query1, ob['_id'])
                response2 = connection.execute(query2, ob['_id'])
                duedate = response2.fetchone()
                print(duedate)
                if response1.fetchone() is None and duedate is not None: #if borrowed
                    ob['availability'] = "No"
                    ob['duedate'] = str(duedate[0])
                elif response1.fetchone() is None and duedate is  None: #does not exist
                    ob['availability'] = "No"
                    ob['duedate'] = "NIL"
                else:
                    ob['availability'] = "Yes"
                    ob['duedate'] = "NIL"
                result2.append(ob)
            result = result2

        if category:
            collection.drop_indexes()
            collection.create_index([('categories', TEXT)], default_language='english')
            r3 = collection.find({"$text": {"$search": category}})
            for ob in r3:
                query1 = "SELECT * FROM book WHERE bookID = %s AND BorrowStatus = 0 AND ReserveStatus = 0"
                query2 = "SELECT DUEDATE FROM Book where BookID = %s"
                response1 = connection.execute(query1, ob['_id'])
                response2 = connection.execute(query2, ob['_id'])
                duedate = response2.fetchone()
                print(duedate)
                if response1.fetchone() is None and duedate is not None: #if borrowed
                    ob['availability'] = "No"
                    ob['duedate'] = str(duedate[0])
                elif response1.fetchone() is None and duedate is  None: #does not exist
                    ob['availability'] = "No"
                    ob['duedate'] = "NIL"
                else:
                    ob['availability'] = "Yes"
                    ob['duedate'] = "NIL"
                result3.append(ob)
            result = result3

        if publishedDate:
            collection.drop_indexes()
            collection.create_index([('publishedDate', TEXT)], default_language='english')
            r4 = collection.find({"$text": {"$search": publishedDate}})
            for ob in r4:
                query1 = "SELECT * FROM book WHERE bookID = %s AND BorrowStatus = 0 AND ReserveStatus = 0"
                query2 = "SELECT DUEDATE FROM Book where BookID = %s"
                response1 = connection.execute(query1, ob['_id'])
                response2 = connection.execute(query2, ob['_id'])
                duedate = response2.fetchone()
                print(duedate)
                if response1.fetchone() is None and duedate is not None: #if borrowed
                    ob['availability'] = "No"
                    ob['duedate'] = str(duedate[0])
                elif response1.fetchone() is None and duedate is  None: #does not exist
                    ob['availability'] = "No"
                    ob['duedate'] = "NIL"
                else:
                    ob['availability'] = "Yes"
                    ob['duedate'] = "NIL"
                result4.append(ob)
            result = result4

        if result1 and result2:
            result = [x for x in result1 if x in result2]

        if result1 and result3:
            result = [x for x in result1 if x in result3]

        if result1 and result4:
            result = [x for x in result1 if x in result4]

        if result2 and result3:
            result = [x for x in result2 if x in result3]

        if result2 and result4:
            result = [x for x in result2 if x in result4]

        if result3 and result4:
            result = [x for x in result3 if x in result4]

        if result1 and result2 and result3:
            resulta = [x for x in result1 if x in result2]
            result = [x for x in resulta if x in result3]

        if result1 and result2 and result4:
            resulta = [x for x in result1 if x in result2]
            result = [x for x in resulta if x in result4]

        if result1 and result3 and result4:
            resulta = [x for x in result1 if x in result3]
            result = [x for x in resulta if x in result4]

        if result2 and result3 and result4:
            resulta = [x for x in result2 if x in result3]
            result = [x for x in resulta if x in result4]

        if result1 and result2 and result3 and result4:
            resulta = [x for x in result1 if x in result2]
            resultb = [x for x in resulta if x in result3]
            result = [x for x in resultb if x in result4]

        if result:
            return render_template('result.html', result=result)
        else:
            flash("No book found. Did you misspell the keywords?")
            # return "No book found. Did you misspell the keywords?", 400
            return redirect('/adsearch')
    else:
        flash("Invalid input, please re-enter!")
        return redirect('/adsearch')





def borrowed():
    if request.method == 'POST':
        if form.request['borrow']:
            return redirect('borrow.html')
        if form.request['reserve']:
            return redirect('reserve.html')
    else:
        render_template('result.html', result=result)


@app.route('/borrow', methods=['POST', 'GET'])
def borrowresults():
    BookID = request.form.get("Borrow")
    UserID = session['user_id']
    display = ''
    query1 = "SELECT * FROM book WHERE bookID = %s AND BorrowStatus = 0 AND ReserveStatus = 0"
    response1 = connection.execute(query1, BookID)
    if (str(response1.fetchone()) == "None"):
        display = "Unfortunately the book that you are trying to borrow is currently not available"
    else:
        query2 = "SELECT amount FROM fine WHERE userID = %s"
        response2 = connection.execute(query2, UserID)
        if (str(response2.fetchone()) != '(0,)'):
            display = "Please pay any outstanding fines before borrowing"
        else:
            query3 = "SELECT *, DATEDIFF(DueDate, (CURDATE())) AS DaysRemaining FROM book WHERE borrow_userID = %s HAVING DaysRemaining < 0"
            response3 = connection.execute(query3, UserID)
            if (len(response3.fetchall()) > 0):
                display = "Seems like you have a book overdue! Return the book before borrowing"
            else:
                query4 = "SELECT COUNT(bookID) AS NumBooksBorrowed FROM book WHERE borrow_userID = %s"
                response4 = connection.execute(query4, UserID)
                check = response4.fetchall()
                if (check[0][0] >= 4):
                    display = "Maximum number of books borrowed already."
                else:
                    query5 = "UPDATE book SET BorrowStatus = 1, borrow_userID = %s ,BorrowDate = CURDATE(), DueDate = DATE_ADD(CURDATE(), INTERVAL 28 DAY) WHERE bookID = %s"  # UserID and BookID to be entered by the user
                    execute5 = connection.execute(query5, UserID, BookID)
                    display = "You have successfully borrowed the book!"
    return render_template('borrow.html', display=display)


@app.route('/reserve', methods=['POST', 'GET'])
def reserveresults():
    BookID = request.form.get("Reserve")
    UserID = session['user_id']
    print(UserID)
    print(BookID)
    display = ''
    query1 = "SELECT * FROM book WHERE bookID = %s AND ReserveStatus = 0 AND BorrowStatus = 1"
    response1 = connection.execute(query1, BookID)
    result = response1.fetchone()
    if (result is None):
        display = "Unfortunately the book that you are trying to reserve is currently not available for reservation"
    else:
        query2 = "SELECT amount FROM user INNER JOIN fine ON user.userID = fine.userID WHERE user.userID = %s"
        response2 = connection.execute(query2, UserID)
        if (str(response2.fetchone()) != "(0,)"):
            display = "Please pay any outstanding fines before reserving"
        else:
            query3 = "SELECT *, DATEDIFF(DueDate, (CURDATE())) AS DaysRemaining FROM book WHERE book.borrow_userID = %s HAVING DaysRemaining < 0"
            response3 = connection.execute(query3, UserID)
            if (len(response3.fetchall()) > 0):
                display = "Seems like you have a book overdue! Return the book before reserving"
            else:
                checkborrowID = "SELECT borrow_userID FROM book WHERE bookID = %s"
                checkcheckborrow = connection.execute(checkborrowID, BookID)
                tocheck = checkcheckborrow.fetchone()[0]
                if UserID == tocheck:
                    display = "You have already borrowed the book"
                else:
                    query5 = "UPDATE book SET ReserveStatus = 1,reserve_userID = %s, ReservationDate = CURDATE() WHERE bookID = %s"
                    execute5 = connection.execute(query5, UserID, BookID)
                    display = "You have successfully reserved the book!"
    print(display)
    return render_template('reserve.html', display=display)

@app.route('/fines', methods=['POST', 'GET'])
def showfine():
    UserID = session['user_id']
    query = "SELECT amount FROM fine WHERE userID = %s"
    response = connection.execute(query, UserID)
    fine = str(response.fetchone()[0])
    return render_template('fines.html', fine=fine)


@app.route('/pay<fine>', methods=['POST', 'GET'])
def payfine(fine):
    today=date.today()
    day= today.strftime("%Y-%m-%d")
    payMethod = str(request.form.get('method'))
    UserId = session['user_id']
    fineamount=int(fine)
    if fineamount == 0:
        flash("You do not have any outstanding fines")
    else:
        query2 = "INSERT INTO Payment(userID, payMethod, PayTime, PayAmount) VALUES (%s, %s , (%s), %s)"
        response = connection.execute(query2, UserId, payMethod, day, fineamount)
        query1 = "UPDATE fine SET amount = 0 WHERE userID = %s"
        payfine= connection.execute(query1, UserId)
        flash("You have successfully paid your fine!")
    return showfine()


if __name__ == "__main__":
    app.run(debug=True)

