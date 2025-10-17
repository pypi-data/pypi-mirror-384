CREATE TABLE `sskm` (
  `id` int(11) NOT NULL,
  `id_users` int(11) NOT NULL DEFAULT '1',
  `Auftragskonto` varchar(100) DEFAULT NULL,
  `Buchungstag` date DEFAULT NULL,
  `Valutadatum` date DEFAULT NULL,
  `Buchungstext` varchar(100) DEFAULT NULL,
  `Verwendungszweck` varchar(300) DEFAULT NULL,
  `Glaeubiger` varchar(100) DEFAULT NULL,
  `Mandatsreferenz` varchar(100) DEFAULT NULL,
  `Kundenreferenz` varchar(100) DEFAULT NULL,
  `Sammlerreferenz` varchar(100) DEFAULT NULL,
  `Lastschrift` varchar(100) DEFAULT NULL,
  `Auslagenersatz` varchar(100) DEFAULT NULL,
  `Beguenstigter` varchar(100) DEFAULT NULL,
  `IBAN` varchar(100) DEFAULT NULL,
  `BIC` varchar(100) DEFAULT NULL,
  `Betrag` decimal(10,5) DEFAULT NULL,
  `Waehrung` varchar(100) DEFAULT NULL,
  `Info` varchar(100) DEFAULT NULL,
  `myconto` varchar(100) DEFAULT NULL,
  `id_plan_vs_real` int(10) DEFAULT NULL,
  `inptimestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `path2inp` text NOT NULL,
  `row_no` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

ALTER TABLE `sskm`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `sskm`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;
