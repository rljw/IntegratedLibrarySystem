# Integrated Library System Application
## BT2102: Data Management and Visualisation (AY20/21 Sem2)

This repository contains an Integrated Library System database application that was built over 5 weeks as part of a group assignment in the module BT2102: Data Management and Visualisation that I took in the National University of Singapore's School of Computing.

Tech Stack: 
- Python
- Flask
- MySQL
- MongoDB
- HTML & CSS

### About
The City Library Web Application is an integrated library system database to manage library operations, such as book borrowing, returning and other operations efficiently and effectively.

### Functionalities of the app
1. User registration

Each new user signs up as a member with a unique 4-character user ID

2. User login

Authenticiate user logins with user ID and password

3. Book search

Users can perform simple search and/or advanced search to locate the book they are looking for. Simple search allows users to search by book titles, while advanced search allows users to search with book title, author name, category or published year.
From there they can proceed to either proceed or reserve books, if their profile permits so.

4. Book borrowing

Each user is allowed to borrow a maximum of 4 books at a time. Users are not allowed to borrow books if they have incurred fines for overdue books.
For each borrowed book, a user is also entitled to one extension of the book's due date

5. Book Reservation

A borrowed book can be reserved by a maximum of one other user. 

6. Fines and Payments

City Library charges a fine of $1 per book per day for overdue books. Outstanding reservations will be cancelled once a user incurs a fine.
Fines can be paid with credit or debit card

7. Administrative User

There is an admin user that can be accessed by City Library staff to get an overview on the status of books in the library and members info.

#### Collaborators:
Renee Lee,
Amanda Lim Jia Wen,
Ong Sijie Grace,
Rhea Sharma,
Tan Kok Lee,
Li Zilu
