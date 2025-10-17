CREATE TABLE IF NOT EXISTS  `imported_csv` (
  `id` int(11) NOT NULL,
  `id_users` int(11) NOT NULL DEFAULT '1',
  `inptimestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `banca` varchar(50) NOT NULL,
  `start` date NOT NULL,
  `end` date NOT NULL,
  `total_rows` int(11) NOT NULL,
  `imported_rows` int(11) NOT NULL,
  `file` longblob NOT NULL,
  `file_name` varchar(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

ALTER TABLE `imported_csv`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `imported_csv`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1;
