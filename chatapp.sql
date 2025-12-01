-- phpMyAdmin SQL Dump
-- version 5.2.2-1.fc40
-- https://www.phpmyadmin.net/
--
-- Hôte : localhost
-- Généré le : lun. 01 déc. 2025 à 20:47
-- Version du serveur : 10.11.11-MariaDB
-- Version de PHP : 8.3.20

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de données : `chatapp`
--

-- --------------------------------------------------------

--
-- Structure de la table `friendships`
--

CREATE TABLE `friendships` (
  `id` int(11) NOT NULL,
  `user_id` int(11) NOT NULL,
  `friend_id` int(11) NOT NULL,
  `status` enum('pending','accepted','blocked') DEFAULT 'pending',
  `requested_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `friendships`
--

INSERT INTO `friendships` (`id`, `user_id`, `friend_id`, `status`, `requested_at`) VALUES
(1, 2, 1, 'accepted', '2025-12-01 19:38:33'),
(2, 1, 3, 'accepted', '2025-12-01 20:45:46');

-- --------------------------------------------------------

--
-- Structure de la table `messages`
--

CREATE TABLE `messages` (
  `id` int(11) NOT NULL,
  `sender_id` int(11) NOT NULL,
  `receiver_id` int(11) NOT NULL,
  `message` text NOT NULL,
  `sent_at` timestamp NULL DEFAULT current_timestamp(),
  `is_read` tinyint(1) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `messages`
--

INSERT INTO `messages` (`id`, `sender_id`, `receiver_id`, `message`, `sent_at`, `is_read`) VALUES
(1, 1, 2, 'Bonjour', '2025-12-01 19:39:04', 0),
(2, 2, 1, 'Ton oncle', '2025-12-01 19:40:00', 0),
(3, 1, 2, 'Ehhh', '2025-12-01 19:42:17', 0),
(4, 1, 2, 'oui oui', '2025-12-01 20:17:51', 0),
(5, 1, 2, 'd', '2025-12-01 20:17:58', 0),
(6, 2, 1, 'salut', '2025-12-01 20:38:10', 0),
(7, 2, 1, 'Yo', '2025-12-01 20:38:18', 0),
(8, 1, 2, 'Ni ?', '2025-12-01 20:40:24', 0),
(9, 2, 1, 'Ehh', '2025-12-01 20:40:33', 0);

-- --------------------------------------------------------

--
-- Structure de la table `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `prenom` varchar(50) NOT NULL,
  `nom` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Déchargement des données de la table `users`
--

INSERT INTO `users` (`id`, `prenom`, `nom`, `email`, `password_hash`, `created_at`) VALUES
(1, 'Max', 'Mbomba', 'max@gmail.com', 'scrypt:32768:8:1$apCtZkPLNxdWaAtc$59dd32882ce70dcc1366c9c22032e1735dccce15ace5e682307d80ea9e7a45f71ffb711daf4942ba657d5db72b7814422da7ce25ab9ee13d513127d8dda999fb', '2025-12-01 19:37:32'),
(2, 'Jo', 'Kapend', 'kap@gmail.com', 'scrypt:32768:8:1$NoVFNgOVrx5scz7d$76c00585923c524eeeea74a4c6298dcc9329aca9be635074131203ee17039a952f40cf4260d16cf979d9d59b4fbd8f82431dc84fe6e90c54a81bc26f2cb0d547', '2025-12-01 19:38:20'),
(3, 'Jc', 'Yizila', 'JC@gmail.com', 'scrypt:32768:8:1$hXLN4I4qrEzStrNG$dd134e2740a61865251a41b8da3ce93e16b0a7391fe0297754d4df58653fb9d90404e8445b36dfb3141037be6c9e3ae75c8a129bd80db3ffa3b855c654dc5dd9', '2025-12-01 20:43:54');

--
-- Index pour les tables déchargées
--

--
-- Index pour la table `friendships`
--
ALTER TABLE `friendships`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `user_id` (`user_id`,`friend_id`),
  ADD KEY `friend_id` (`friend_id`);

--
-- Index pour la table `messages`
--
ALTER TABLE `messages`
  ADD PRIMARY KEY (`id`),
  ADD KEY `sender_id` (`sender_id`),
  ADD KEY `receiver_id` (`receiver_id`);

--
-- Index pour la table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT pour les tables déchargées
--

--
-- AUTO_INCREMENT pour la table `friendships`
--
ALTER TABLE `friendships`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT pour la table `messages`
--
ALTER TABLE `messages`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT pour la table `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Contraintes pour les tables déchargées
--

--
-- Contraintes pour la table `friendships`
--
ALTER TABLE `friendships`
  ADD CONSTRAINT `friendships_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `friendships_ibfk_2` FOREIGN KEY (`friend_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;

--
-- Contraintes pour la table `messages`
--
ALTER TABLE `messages`
  ADD CONSTRAINT `messages_ibfk_1` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `messages_ibfk_2` FOREIGN KEY (`receiver_id`) REFERENCES `users` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
