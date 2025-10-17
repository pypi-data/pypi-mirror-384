CREATE TABLE `plan_vs_real` (
  `id` int(11) NOT NULL,
  `id_users` int(11) NOT NULL DEFAULT '1',
  `inptimestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `id_ch_pl` int(11) NOT NULL,
  `category` varchar(50) DEFAULT NULL,
  `myconto` varchar(100) DEFAULT NULL,
  `name` varchar(100) DEFAULT NULL,
  `plannedvalue` decimal(10,5) DEFAULT NULL,
  `bank_table` varchar(100) NOT NULL,
  `id_bank_table` int(11) NOT NULL,
  `Buchungstag` date DEFAULT NULL,
  `Betrag` decimal(10,5) DEFAULT NULL,
  `PaymentReference` text,
  `PartnerName` varchar(300) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;


ALTER TABLE `plan_vs_real`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `plan_vs_real`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=651;
