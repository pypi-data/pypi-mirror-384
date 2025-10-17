-- phpMyAdmin SQL Dump
-- version 5.1.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost:3306
-- Generation Time: Sep 16, 2024 at 01:40 PM
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
  `doc_path` text NOT NULL,
  `dd` enum('male','fem') NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `ids`
  ADD PRIMARY KEY (`id`),
  ADD KEY `documente_foreign` (`documente_id`);

ALTER TABLE `ids`
  MODIFY `id` int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;
COMMIT;
