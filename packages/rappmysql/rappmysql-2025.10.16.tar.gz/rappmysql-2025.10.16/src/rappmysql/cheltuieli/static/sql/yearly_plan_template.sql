
CREATE TABLE `yearly_plan` (
  `id` int(11) NOT NULL,
  `id_users` int(11) NOT NULL,
  `inptimestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `db_update` int(11) DEFAULT NULL,
  `myconto` varchar(100) DEFAULT NULL,
  `expenses` varchar(100) DEFAULT NULL,
  `January` decimal(10,5) DEFAULT NULL,
  `February` decimal(10,5) DEFAULT NULL,
  `March` decimal(10,5) DEFAULT NULL,
  `April` decimal(10,5) DEFAULT NULL,
  `May` decimal(10,5) DEFAULT NULL,
  `June` decimal(10,5) DEFAULT NULL,
  `July` decimal(10,5) DEFAULT NULL,
  `August` decimal(10,5) DEFAULT NULL,
  `September` decimal(10,5) DEFAULT NULL,
  `October` decimal(10,5) DEFAULT NULL,
  `November` decimal(10,5) DEFAULT NULL,
  `December` decimal(10,5) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=latin1;

ALTER TABLE `yearly_plan`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `yearly_plan`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=19;
