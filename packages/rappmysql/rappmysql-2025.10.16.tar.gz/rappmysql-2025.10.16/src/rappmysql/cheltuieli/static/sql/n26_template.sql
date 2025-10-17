CREATE TABLE `n26` (
  `id` int(11) NOT NULL,
  `id_users` int(11) NOT NULL DEFAULT '1',
  `Buchungstag` date DEFAULT NULL,
  `ValueDate` date DEFAULT NULL,
  `Beguenstigter` varchar(100) DEFAULT NULL,
  `IBAN` varchar(100) DEFAULT NULL,
  `Type` varchar(300) DEFAULT NULL,
  `PaymentReference` varchar(100) DEFAULT NULL,
  `AccountName` varchar(100) DEFAULT NULL,
  `Amount` decimal(10,5) DEFAULT NULL,
  `OriginalAmount` varchar(100) DEFAULT NULL,
  `OriginalCurrency` varchar(100) DEFAULT NULL,
  `ExchangeRate` varchar(100) DEFAULT NULL,
  `myconto` varchar(100) DEFAULT NULL,
  `id_plan_vs_real` int(10) DEFAULT NULL,
  `inptimestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `path2inp` mediumtext NOT NULL,
  `row_no` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `n26`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `n26`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;
