-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Sep 16, 2024 at 01:34 PM
-- Server version: 8.0.22
-- PHP Version: 8.0.9

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `aaa`
--

-- --------------------------------------------------------

--
-- Table structure for table `ids`
--

CREATE TABLE `ids` (
  `id` int NOT NULL,
  `documente_id` int NOT NULL DEFAULT '10',
  `name` varchar(100) NOT NULL,
  `valid_from` date DEFAULT NULL,
  `valid_to` date DEFAULT NULL,
  `auto_ext` tinyint(1) DEFAULT NULL,
  `file_doc` longblob NOT NULL,
  `file_type` varchar(50) NOT NULL,
  `path` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dumping data for table `ids`
--

INSERT INTO `ids` (`id`, `documente_id`, `name`, `valid_from`, `valid_to`, `auto_ext`, `file_doc`, `file_type`, `path`) VALUES
(1, 9, 'Buletin', '2010-12-09', '2017-12-02', NULL, '', '', '\"D:\\Documente\\AAA\\Buletin Radu Mircea_bis 2017.pdf\"'),
(2, 9, 'Buletin', '2017-03-08', '2027-12-02', NULL, '', '', '\"D:\\Documente\\AAA\\Buletin Radu Mircea_bis 2027.pdf\"'),
(3, 9, 'BuletinTata', '2011-11-27', '2071-10-27', NULL, '', '', '\"D:\\Documente\\AAA\\Buletine.pdf\"'),
(4, 9, 'BuletinMama', '2013-07-19', '2023-04-13', NULL, '', '', '\"D:\\Documente\\AAA\\Buletine.pdf\"'),
(5, 9, 'Certificat_Celibat', NULL, NULL, NULL, '', '', '\"D:\\Documente\\AAA\\Certificat_Celibat.pdf\"'),
(6, 9, 'Certificat_de_Nastere_OLD', '1986-09-12', NULL, NULL, '', '', '\"D:\\Documente\\AAA\\Certificat_de_Nastere_OLD.pdf\"'),
(7, 9, 'Certificat_de_Nastere', '2021-04-08', NULL, NULL, '', '', '\"D:\\Documente\\AAA\\Certificat_de_Nastere.pdf\"'),
(8, 9, 'Passpot Radu Mircea_bis 2012', '2007-05-29', '2012-05-29', NULL, '', '', '\"D:\\Documente\\AAA\\Passpot Radu Mircea_bis 2012.PDF\"'),
(9, 9, 'Passpot Radu Mircea_bis 2017', '2012-02-21', '2017-02-21', NULL, '', '', '\"D:\\Documente\\AAA\\Passpot Radu Mircea_bis 2017.pdf\"'),
(10, 9, 'Passpot Radu Mircea_bis 2017', '2017-04-21', '2022-04-21', NULL, '', '', '\"D:\\Documente\\AAA\\Passpot Radu Mircea_bis 2022.pdf\"');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `ids`
--
ALTER TABLE `ids`
  ADD PRIMARY KEY (`id`),
  ADD KEY `documente_foreign` (`documente_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `ids`
--
ALTER TABLE `ids`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
