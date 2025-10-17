CREATE TABLE `deubnk` (
  `id` int(11) NOT NULL,
  `id_users` int(11) NOT NULL DEFAULT '1',
  `Buchungstag` date DEFAULT NULL,
  `Valuedate` date DEFAULT NULL,
  `TransactionType` varchar(100) DEFAULT NULL,
  `Beguenstigter` varchar(300) DEFAULT NULL,
  `Verwendungszweck` mediumtext,
  `IBAN` varchar(100) DEFAULT NULL,
  `BIC` varchar(100) DEFAULT NULL,
  `CustomerReference` varchar(100) DEFAULT NULL,
  `Mandatsreferenz` varchar(100) DEFAULT NULL,
  `CreditorID` varchar(100) DEFAULT NULL,
  `Compensationamount` varchar(100) DEFAULT NULL,
  `OriginalAmount` varchar(100) DEFAULT NULL,
  `Ultimatecreditor` varchar(100) DEFAULT NULL,
  `Ultimatedebtor` varchar(100) DEFAULT NULL,
  `Numberoftransactions` varchar(100) DEFAULT NULL,
  `Numberofcheques` varchar(100) DEFAULT NULL,
  `Debit` decimal(10,5) DEFAULT NULL,
  `Credit` decimal(10,5) DEFAULT NULL,
  `Currency` varchar(100) DEFAULT NULL,
  `myconto` varchar(100) DEFAULT NULL,
  `id_plan_vs_real` int(10) DEFAULT NULL,
  `inptimestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `path2inp` mediumtext NOT NULL,
  `row_no` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `deubnk`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `deubnk`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;

