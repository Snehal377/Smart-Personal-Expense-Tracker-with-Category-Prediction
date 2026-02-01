CREATE DATABASE IF NOT EXISTS live_data_project;

USE live_data_project;

CREATE TABLE IF NOT EXISTS transactions (
    transaction_id INT AUTO_INCREMENT PRIMARY KEY,
    
    user_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    total DECIMAL(10,2) AS (quantity * price) STORED,
    transaction_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_transaction(user_id, product_id, transaction_time)
);

CREATE TABLE Category (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    Category_name VARCHAR(50) NOT NULL,         -- e.g., Food, Travel, Shopping
    Descriptions VARCHAR(255)           -- optional general description
);
INSERT INTO Category (Category_name, Descriptions) VALUES
('Food', 'Meals, Snacks, Drinks'),
('Travel', 'Train, Flight, Taxi, Bus'),
('Shopping', 'Clothes, Shoes, Accessories'),
('Electronics', 'Phone, Laptop, Gadgets'),
('Others', 'Miscellaneous expenses');

select * from Category;

ALTER TABLE transactions
ADD COLUMN category_id INT,
ADD CONSTRAINT fk_Category
    FOREIGN KEY (category_id)
    REFERENCES Category(category_id);


ALTER TABLE transactions
MODIFY COLUMN user_id VARCHAR(100) NOT NULL;

ALTER TABLE transactions
MODIFY COLUMN product_id VARCHAR(100);

USE live_data_project;

SELECT * FROM transactions ORDER BY transaction_time DESC;

select distinct(transaction_id) from transactions;

select count(transaction_id) from transactions;

-- Food
UPDATE transactions
SET category_id = 1
WHERE price < 0
  AND category_id IS NULL
  AND (
       description LIKE '%Lunch%'
    OR description LIKE '%Snacks%'
    OR description LIKE '%Drinks%'
  );



-- Travel
UPDATE transactions
SET category_id = 2
WHERE price < 0 AND description LIKE '%Train%'
   OR description LIKE '%Flight%'
   OR description LIKE '%Taxi%'
   OR description LIKE '%Bus%'
   OR description LIKE '%Ticket%';

-- Shopping
UPDATE transactions
SET category_id = 3
WHERE price < 0 AND description LIKE '%Clothes%'
   OR description LIKE '%Shoes%'
   OR description LIKE '%Accessories%';

-- Electronics
UPDATE transactions
SET category_id = 4
WHERE price < 0 AND description LIKE '%Phone%'
   OR description LIKE '%Laptop%'
   OR description LIKE '%Gadgets%';

-- Others (anything else negative)
UPDATE transactions
SET category_id = 5
WHERE price < 0 AND category_id IS NULL;


--  fill describe column value 

UPDATE transactions
SET description =
CASE
    WHEN price < 0 AND ABS(price) <= 100 THEN 'Snacks'
    WHEN price < 0 AND ABS(price) BETWEEN 101 AND 500 THEN 'Lunch'
    WHEN price < 0 AND ABS(price) BETWEEN 501 AND 2000 THEN 'Shopping'
    WHEN price < 0 AND ABS(price) > 2000 THEN 'Electronics'
    ELSE NULL
END
WHERE description IS NULL;

UPDATE transactions
SET description =
CASE
    WHEN ABS(price) <= 50 THEN 'Snacks'
    WHEN ABS(price) BETWEEN 51 AND 300 THEN 'Lunch'
    WHEN ABS(price) BETWEEN 301 AND 1500 THEN 'Shopping'
    ELSE 'Electronics'
END
WHERE price < 0
  AND description IS NULL;

SELECT transaction_id, price, description
FROM transactions
ORDER BY category_id DESC
LIMIT 50000;

-- Food
UPDATE transactions
SET category_id = 1
WHERE description IN ('Snacks', 'Lunch');

-- Shopping
UPDATE transactions
SET category_id = 3
WHERE description = 'Shopping';

-- Electronics
UPDATE transactions
SET category_id = 4
WHERE description = 'Electronics';

-- Others (fallback)
UPDATE transactions
SET category_id = 5
WHERE price < 0 AND category_id IS NULL;

-- 

SELECT price, description, category_id
FROM transactions
WHERE price < 0;

INSERT INTO transactions (
    user_id, quantity, price, transaction_time, product_id, description
) VALUES (
    1, 1, -2000, NOW(), 1, 'Laptop Purchase'
);

UPDATE transactions
SET category_id = 4
WHERE price < 0 AND description LIKE '%Laptop%';

-- Update category_id for all transactions at once
UPDATE transactions
SET category_id = CASE
    -- Food: Snacks, Lunch
    WHEN price < 0 AND description IN ('Snacks', 'Lunch') THEN 1
    -- Shopping
    WHEN price < 0 AND description = 'Shopping' THEN 3
    -- Electronics
    WHEN price < 0 AND description = 'Electronics' THEN 4
    -- Others: Any other negative price not yet categorized
    WHEN price < 0 AND category_id IS NULL THEN 5
    ELSE category_id
END;

SELECT price, description, category_id FROM transactions ORDER BY transaction_time DESC LIMIT 50;

UPDATE transactions
SET category_id = CASE
    WHEN price < 0 AND ABS(price) <= 50 THEN 1   -- Food: Snacks
    WHEN price < 0 AND ABS(price) BETWEEN 51 AND 300 THEN 1  -- Food: Lunch
    WHEN price < 0 AND ABS(price) BETWEEN 301 AND 1500 THEN 3  -- Shopping
    WHEN price < 0 AND ABS(price) > 1500 THEN 4  -- Electronics
    ELSE category_id
END,
description = CASE
    WHEN price < 0 AND ABS(price) <= 50 THEN 'Snacks'
    WHEN price < 0 AND ABS(price) BETWEEN 51 AND 300 THEN 'Lunch'
    WHEN price < 0 AND ABS(price) BETWEEN 301 AND 1500 THEN 'Shopping'
    WHEN price < 0 AND ABS(price) > 1500 THEN 'Electronics'
    ELSE description
END
WHERE price < 0;

-- 


-- 1️⃣ Update all existing negative transactions
UPDATE transactions
SET 
    category_id = CASE
        WHEN price < 0 AND ABS(price) <= 50 THEN 1   -- Food: Snacks
        WHEN price < 0 AND ABS(price) BETWEEN 51 AND 300 THEN 1  -- Food: Lunch
        WHEN price < 0 AND ABS(price) BETWEEN 301 AND 1500 THEN 3  -- Shopping
        WHEN price < 0 AND ABS(price) > 1500 THEN 4  -- Electronics
        ELSE category_id
    END,
    description = CASE
        WHEN price < 0 AND ABS(price) <= 50 THEN 'Snacks'
        WHEN price < 0 AND ABS(price) BETWEEN 51 AND 300 THEN 'Lunch'
        WHEN price < 0 AND ABS(price) BETWEEN 301 AND 1500 THEN 'Shopping'
        WHEN price < 0 AND ABS(price) > 1500 THEN 'Electronics'
        ELSE description
    END
WHERE price < 0;

-- ✅ Optional: Verify the updates
SELECT price, description, category_id
FROM transactions
ORDER BY transaction_time DESC
LIMIT 50;


UPDATE transactions
SET 
    category_id = CASE
        WHEN ABS(price) <= 50 THEN 1   -- Food: Snacks
        WHEN ABS(price) BETWEEN 51 AND 300 THEN 1  -- Food: Lunch
        WHEN ABS(price) BETWEEN 301 AND 1500 THEN 3  -- Shopping
        WHEN ABS(price) > 1500 THEN 4  -- Electronics
        ELSE category_id
    END,
    description = CASE
        WHEN ABS(price) <= 50 THEN 'Snacks'
        WHEN ABS(price) BETWEEN 51 AND 300 THEN 'Lunch'
        WHEN ABS(price) BETWEEN 301 AND 1500 THEN 'Shopping'
        WHEN ABS(price) > 1500 THEN 'Electronics'
        ELSE description
    END
WHERE price < 0 AND category_id IS NULL;

SELECT price, description, category_id
FROM transactions
ORDER BY transaction_time DESC
LIMIT 50;

UPDATE transactions
SET 
    category_id = CASE
        WHEN ABS(price) <= 50 THEN 1   -- Food: Snacks
        WHEN ABS(price) BETWEEN 51 AND 300 THEN 1  -- Food: Lunch
        WHEN ABS(price) BETWEEN 301 AND 1500 THEN 3  -- Shopping
        WHEN ABS(price) > 1500 THEN 4  -- Electronics
        ELSE category_id
    END,
    description = CASE
        WHEN ABS(price) <= 50 THEN 'Snacks'
        WHEN ABS(price) BETWEEN 51 AND 300 THEN 'Lunch'
        WHEN ABS(price) BETWEEN 301 AND 1500 THEN 'Shopping'
        WHEN ABS(price) > 1500 THEN 'Electronics'
        ELSE description
    END
WHERE price < 0;

UPDATE transactions
SET 
    category_id = CASE
        WHEN ABS(price) <= 50 THEN 1
        WHEN ABS(price) BETWEEN 51 AND 300 THEN 1
        WHEN ABS(price) BETWEEN 301 AND 1500 THEN 3
        WHEN ABS(price) > 1500 THEN 4
    END,
description = CASE
        WHEN ABS(price) <= 50 THEN 'Snacks'
        WHEN ABS(price) BETWEEN 51 AND 300 THEN 'Lunch'
        WHEN ABS(price) BETWEEN 301 AND 1500 THEN 'Shopping'
        WHEN ABS(price) > 1500 THEN 'Electronics'
END
WHERE price < 0 AND category_id IS NULL;
UPDATE transactions
SET category_id = 3, description = 'Shopping'
WHERE price = -500;

UPDATE transactions
SET category_id = 4, description = 'Electronics'
WHERE price = -2000;

SELECT price, description, category_id
FROM transactions
WHERE price IN (-500, -2000);

UPDATE transactions
SET
    category_id = CASE
        WHEN price < 0 AND ABS(price) <= 50 THEN 1
        WHEN price < 0 AND ABS(price) BETWEEN 51 AND 300 THEN 1
        WHEN price < 0 AND ABS(price) BETWEEN 301 AND 1500 THEN 3
        WHEN price < 0 AND ABS(price) > 1500 THEN 4
        ELSE category_id
    END,
    description = CASE
        WHEN price < 0 AND ABS(price) <= 50 THEN 'Snacks'
        WHEN price < 0 AND ABS(price) BETWEEN 51 AND 300 THEN 'Lunch'
        WHEN price < 0 AND ABS(price) BETWEEN 301 AND 1500 THEN 'Shopping'
        WHEN price < 0 AND ABS(price) > 1500 THEN 'Electronics'
        ELSE description
    END;
    
    SELECT COUNT(*) 
FROM transactions 
WHERE price < 0 AND (category_id IS NULL OR description IS NULL);

DELIMITER $$

CREATE TRIGGER trg_auto_category
BEFORE INSERT ON transactions
FOR EACH ROW
BEGIN
    -- Only for EXPENSE
    IF NEW.price < 0 THEN

        IF ABS(NEW.price) <= 50 THEN
            SET NEW.category_id = 1;
            SET NEW.description = 'Snacks';

        ELSEIF ABS(NEW.price) BETWEEN 51 AND 300 THEN
            SET NEW.category_id = 1;
            SET NEW.description = 'Lunch';

        ELSEIF ABS(NEW.price) BETWEEN 301 AND 1500 THEN
            SET NEW.category_id = 3;
            SET NEW.description = 'Shopping';

        ELSEIF ABS(NEW.price) > 1500 THEN
            SET NEW.category_id = 4;
            SET NEW.description = 'Electronics';
        END IF;

    END IF;
END$$

DELIMITER ;

INSERT INTO transactions
(user_id, quantity, price, transaction_time, product_id)
VALUES
(1, 1, -40,  NOW(), 1),
(1, 1, -200, NOW() + INTERVAL 1 SECOND, 1),
(1, 1, -900, NOW() + INTERVAL 2 SECOND, 1),
(1, 1, -2500,NOW() + INTERVAL 3 SECOND, 1);

SELECT price, description, category_id
FROM transactions
ORDER BY transaction_time DESC
LIMIT 10;

SELECT DISTINCT category_id FROM transactions;

SELECT category_id FROM category;

SELECT t.transaction_id,t.quantity,t.price,t.total,t.transaction_time,t.product_id,
c.Category_name AS Category
FROM transactions t
LEFT JOIN Category c
ON t.category_id = c.category_id ;

