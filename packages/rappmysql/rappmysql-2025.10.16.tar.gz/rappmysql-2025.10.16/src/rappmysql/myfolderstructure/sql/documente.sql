-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Sep 16, 2024 at 01:23 PM
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
-- Database: `myfolderstructure`
--

-- --------------------------------------------------------

--
-- Table structure for table `documente`
--

CREATE TABLE `documente` (
  `id` int NOT NULL,
  `LastModification` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `Name` varchar(50) NOT NULL,
  `NoOfDocuments` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

--
-- Dumping data for table `documente`
--

INSERT INTO `documente` (`id`, `LastModification`, `Name`, `NoOfDocuments`) VALUES
(1, '2021-08-29 14:52:12', 'Aeroclub', NULL),
(2, '2021-08-29 14:52:53', 'Apartament', NULL),
(3, '2021-08-29 14:53:19', 'Asigurari', NULL),
(4, '2021-08-29 14:53:48', 'Banca', NULL),
(5, '2021-08-29 14:54:35', 'Masina', NULL),
(6, '2021-08-29 14:54:48', 'Munca', NULL),
(7, '2021-08-29 19:11:08', 'Scoala', NULL),
(8, '2021-08-29 19:11:55', 'Stat', NULL),
(9, '2021-10-03 14:12:25', 'IDS', 10);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `documente`
--
ALTER TABLE `documente`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `id` (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `documente`
--
ALTER TABLE `documente`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
