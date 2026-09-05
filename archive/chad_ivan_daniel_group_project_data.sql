CREATE DATABASE  IF NOT EXISTS `dojo_messages` /*!40100 DEFAULT CHARACTER SET utf8 */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `dojo_messages`;
-- MySQL dump 10.13  Distrib 8.0.18, for Win64 (x86_64)
--
-- Host: localhost    Database: dojo_messages
-- ------------------------------------------------------
-- Server version	8.0.18

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `followers`
--

DROP TABLE IF EXISTS `followers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `followers` (
  `follower_id` int(11) NOT NULL,
  `followed_id` int(11) NOT NULL,
  PRIMARY KEY (`follower_id`,`followed_id`),
  KEY `fk_users_has_users_users2_idx` (`followed_id`),
  KEY `fk_users_has_users_users1_idx` (`follower_id`),
  CONSTRAINT `fk_users_has_users_users1` FOREIGN KEY (`follower_id`) REFERENCES `users` (`user_id`),
  CONSTRAINT `fk_users_has_users_users2` FOREIGN KEY (`followed_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `followers`
--

LOCK TABLES `followers` WRITE;
/*!40000 ALTER TABLE `followers` DISABLE KEYS */;
INSERT INTO `followers` VALUES (3,1),(1,2),(2,3);
/*!40000 ALTER TABLE `followers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `keys`
--

DROP TABLE IF EXISTS `keys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `keys` (
  `key_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `user_key` varchar(150) DEFAULT NULL,
  PRIMARY KEY (`key_id`),
  UNIQUE KEY `key_id_UNIQUE` (`key_id`),
  KEY `fk_keys_users1_idx` (`user_id`),
  CONSTRAINT `fk_keys_users1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `keys`
--

LOCK TABLES `keys` WRITE;
/*!40000 ALTER TABLE `keys` DISABLE KEYS */;
INSERT INTO `keys` VALUES (1,1,'6jVQ2j_wO1bQqU0zpv88RKkLSls0UfTMkhao3eBicDU='),(2,2,'Hhc8MhdmAQ5pxWHLm9R4d2NUSR7ys02jXHfcZpst2EE='),(3,3,'wdrqyxmiE9GB33bqL2RjcMjmblbwmXgscWUToCJmqaM=');
/*!40000 ALTER TABLE `keys` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `messages`
--

DROP TABLE IF EXISTS `messages`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `messages` (
  `message_id` int(11) NOT NULL AUTO_INCREMENT,
  `author_id` int(11) NOT NULL,
  `message` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`message_id`),
  UNIQUE KEY `message_id_UNIQUE` (`message_id`),
  KEY `fk_messages_users_idx` (`author_id`),
  CONSTRAINT `fk_messages_users` FOREIGN KEY (`author_id`) REFERENCES `users` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `messages`
--

LOCK TABLES `messages` WRITE;
/*!40000 ALTER TABLE `messages` DISABLE KEYS */;
INSERT INTO `messages` VALUES (1,1,'gAAAAABeNKTnpi0ulx6aGjZasqKrPACLso3YZxr_HAi0PK2seV1RVWU8-9roPX36kCPBl2WhNuTHT0emrhcEHrL6murhO1t_cQ==','2020-01-31 14:06:31','2020-01-31 14:06:31'),(2,2,'gAAAAABeNKT_NtLVr1JNpLenZRuOICbc-GSq30HUT5qc4hUHlRT9DDciMp4jV3GVe1R0KxtNyT0bYk_d2XeWv3IHONET86Yqlw==','2020-01-31 14:06:55','2020-01-31 14:06:55'),(3,3,'gAAAAABeNKUXqhgEqFiPb0iUJ18XsyF269jZq--jtZMIgsdwi56y_P4kQOo7iqXNtL_coSjRo283CturUTaiVx7IAYo-jxwNzg==','2020-01-31 14:07:19','2020-01-31 14:07:19');
/*!40000 ALTER TABLE `messages` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_likes`
--

DROP TABLE IF EXISTS `user_likes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_likes` (
  `user_like_id` int(11) NOT NULL,
  `message_like_id` int(11) NOT NULL,
  PRIMARY KEY (`user_like_id`,`message_like_id`),
  KEY `fk_users_has_messages_messages1_idx` (`message_like_id`),
  KEY `fk_users_has_messages_users1_idx` (`user_like_id`),
  CONSTRAINT `fk_users_has_messages_messages1` FOREIGN KEY (`message_like_id`) REFERENCES `messages` (`message_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_users_has_messages_users1` FOREIGN KEY (`user_like_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_likes`
--

LOCK TABLES `user_likes` WRITE;
/*!40000 ALTER TABLE `user_likes` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_likes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `first_name` varchar(45) DEFAULT NULL,
  `last_name` varchar(45) DEFAULT NULL,
  `email` varchar(45) DEFAULT NULL,
  `password` varchar(63) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `avatar` varchar(255) DEFAULT NULL,
  `bio` longtext,
  PRIMARY KEY (`user_id`),
  UNIQUE KEY `reg_id_UNIQUE` (`user_id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Mike','Jones','m@j.com','$2b$12$NlmCP1c/Myl9MK0Ftgp00.FZv.9vua3hT5vOQYZyeQdHAZDTvgrzq','2020-01-31 14:06:22','2020-01-31 14:06:22',NULL,NULL),(2,'Kanye','West','k@w.com','$2b$12$aO58N6AxJrf2NvmSOkLxNe.564VXvF6keeDES97ZCYRbj1b2lcOLq','2020-01-31 14:06:49','2020-01-31 14:06:49',NULL,NULL),(3,'Jane','Fonda','j@f.com','$2b$12$SXDkOLiYDBa4i3mb4uPJN.1h7S/7hqSE2ubOkBU5Gp2PlkKxgl6J6','2020-01-31 14:07:12','2020-01-31 14:07:12',NULL,NULL);
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2020-01-31 15:55:04
