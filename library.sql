/*!40101 SET NAMES utf8 */;

/*!40101 SET SQL_MODE=''*/;

/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
CREATE DATABASE /*!32312 IF NOT EXISTS*/`library` /*!40100 DEFAULT CHARACTER SET latin1 */;

USE `library`;

/*Table structure for table `customers` */
DROP TABLE IF EXISTS `User`;

CREATE TABLE `User`(
	`userID` VARCHAR(5) NOT NULL,
	`userName` VARCHAR(20) NOT NULL,
    `password` VARCHAR(50) NOT NULL,
    `email` VARCHAR(100),
    `phoneNumber` VARCHAR(8),
	UNIQUE(`userID`),
    primary key (`userID`));
   
    
    
DROP TABLE IF EXISTS `BookAttributes`;
    
CREATE TABLE `BookAttributes`(
    `ISBN` VARCHAR(10) NOT NULL,
	`title` VARCHAR(50) NOT NULL,
    `categories` VARCHAR(10000) NOT NULL,
    `shortDesc` VARCHAR(1000) NOT NULL,
    `longDesc` VARCHAR(100000) NOT NULL,
    `thumbnailURL` VARCHAR(200) NOT NULL,
    `publishedDate` DATE NOT NULL,
    `pgCount` SMALLINT NOT NULL,
    `authors` VARCHAR(1000) NOT NULL,
    UNIQUE(`ISBN`),
    PRIMARY KEY (`ISBN`));
    
DROP TABLE IF EXISTS `Book`;
    
CREATE TABLE `Book`(
	`bookID` VARCHAR(10) NOT NULL,
    `ISBN` VARCHAR(10) NOT NULL,
    `reserve_userID` VARCHAR(5),
    `ReservationDate` DATE,
    `ReserveStatus` SMALLINT CHECK(ReserveStatus IN (0, 1)),
	`borrow_userID` VARCHAR(5),
    `BorrowDate` DATE,
    `ReturnDate` DATE,
    `DueDate` DATE,
    `Extend` SMALLINT CHECK(Extend IN (0, 1)),			#Checks whether user has extended this book. Resets upon return
    `BorrowStatus` SMALLINT CHECK(BorrowStatus IN (0, 1)),
    UNIQUE(`bookID`),
    PRIMARY KEY (`bookID`),
	CONSTRAINT `book_ibfk_1` FOREIGN KEY (`borrow_userID`) REFERENCES `User` (`userID`),
    CONSTRAINT `book_ibfk_2` FOREIGN KEY (`reserve_userID`) REFERENCES `User` (`userID`),
    CONSTRAINT `book_ibfk_3` FOREIGN KEY (`ISBN`) REFERENCES `BookAttributes` (`ISBN`));
    
    
DROP TABLE IF EXISTS `Payment`;

CREATE TABLE `Payment`(
	`TransactionNo` INT NOT NULL AUTO_INCREMENT,
	`userID` VARCHAR(5),
    `payMethod` VARCHAR(6) NOT NULL CHECK(payMethod IN('Credit','Debit')), 
    `PayTime` DATE NOT NULL,
    `PayAmount` INT,
    UNIQUE(`TransactionNo`),
    PRIMARY KEY (`TransactionNo`),
	CONSTRAINT `payment_ibfk_1` FOREIGN KEY (`userID`) REFERENCES `User` (`userID`));
    
DROP TABLE IF EXISTS `Fine`;

CREATE TABLE `Fine` (
	`userID` VARCHAR(5) NOT NULL,
    `amount` INT NOT NULL,
	PRIMARY KEY (`userID`),
    CONSTRAINT `fine_ibfk_1` FOREIGN KEY (`userID`) REFERENCES `User` (`userID`));



