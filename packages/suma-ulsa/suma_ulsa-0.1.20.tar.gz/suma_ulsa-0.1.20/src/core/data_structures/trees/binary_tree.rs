use std::cmp::Ordering;
use std::fmt::Display;

#[derive(Debug, Clone)]
pub struct BinaryTree<T> {
    root: Option<Box<TreeNode<T>>>,
}

#[derive(Debug, Clone)]
pub struct TreeNode<T> {
    pub value: T,
    pub left: Option<Box<TreeNode<T>>>,
    pub right: Option<Box<TreeNode<T>>>,
}

impl<T: Ord + Display + Clone> BinaryTree<T> {
    // CONSTRUCTORES
    pub fn new() -> Self {
        BinaryTree { root: None }
    }

    // OPERACIONES BÁSICAS
    pub fn insert(&mut self, value: T) {
        let new_node = Box::new(TreeNode {
            value,
            left: None,
            right: None,
        });
        
        if self.root.is_none() {
            self.root = Some(new_node);
        } else {
            Self::insert_recursive(&mut self.root, new_node);
        }
    }

    fn insert_recursive(node: &mut Option<Box<TreeNode<T>>>, new_node: Box<TreeNode<T>>) {
        match node {
            Some(ref mut current) => {
                if new_node.value < current.value {
                    Self::insert_recursive(&mut current.left, new_node);
                } else {
                    Self::insert_recursive(&mut current.right, new_node);
                }
            }
            None => *node = Some(new_node),
        }
    }

    pub fn contains(&self, value: T) -> bool {
        Self::search_recursive(&self.root, &value)
    }

    fn search_recursive(node: &Option<Box<TreeNode<T>>>, value: &T) -> bool {
        match node {
            Some(current) => {
                match value.cmp(&current.value) {
                    Ordering::Equal => true,
                    Ordering::Less => Self::search_recursive(&current.left, value),
                    Ordering::Greater => Self::search_recursive(&current.right, value),
                }
            }
            None => false,
        }
    }

    pub fn find(&self, value: &T) -> Option<&TreeNode<T>> {
        Self::find_recursive(&self.root, value)
    }

    fn find_recursive<'a>(node: &'a Option<Box<TreeNode<T>>>, value: &T) -> Option<&'a TreeNode<T>> {
        match node {
            Some(current) => {
                match value.cmp(&current.value) {
                    Ordering::Equal => Some(current),
                    Ordering::Less => Self::find_recursive(&current.left, value),
                    Ordering::Greater => Self::find_recursive(&current.right, value),
                }
            }
            None => None,
        }
    }

    // ELIMINACIÓN
    pub fn remove(&mut self, value: T) -> bool {
        let original_size = self.size();
        self.root = Self::remove_recursive(self.root.take(), value);
        self.size() < original_size
    }

    fn remove_recursive(node: Option<Box<TreeNode<T>>>, value: T) -> Option<Box<TreeNode<T>>> {
        match node {
            Some(mut current) => {
                match value.cmp(&current.value) {
                    Ordering::Less => {
                        current.left = Self::remove_recursive(current.left.take(), value);
                        Some(current)
                    }
                    Ordering::Greater => {
                        current.right = Self::remove_recursive(current.right.take(), value);
                        Some(current)
                    }
                    Ordering::Equal => {
                        // Caso 1: Nodo hoja
                        if current.left.is_none() && current.right.is_none() {
                            None
                        }
                        // Caso 2: Un solo hijo - izquierdo
                        else if current.right.is_none() {
                            current.left.take()
                        }
                        // Caso 2: Un solo hijo - derecho
                        else if current.left.is_none() {
                            current.right.take()
                        }
                        // Caso 3: Dos hijos
                        else {
                            // Encontrar el sucesor in-order (mínimo en el subárbol derecho)
                            let min_value = Self::find_min(&mut current.right).unwrap();
                            current.value = min_value.clone();
                            current.right = Self::remove_recursive(current.right.take(), min_value);
                            Some(current)
                        }
                    }
                }
            }
            None => None,
        }
    }

    fn find_min(node: &mut Option<Box<TreeNode<T>>>) -> Option<T> 
    where
        T: Clone,
    {
        match node {
            Some(current) => {
                if current.left.is_some() {
                    Self::find_min(&mut current.left)
                } else {
                    Some(current.value.clone())
                }
            }
            None => None,
        }
    }

    // RECORRIDOS (TRAVERSALS)
    pub fn in_order(&self) -> Vec<&T> {
        let mut result = Vec::new();
        Self::in_order_traversal(&self.root, &mut result);
        result
    }

    fn in_order_traversal<'a>(node: &'a Option<Box<TreeNode<T>>>, result: &mut Vec<&'a T>) {
        if let Some(current) = node {
            Self::in_order_traversal(&current.left, result);
            result.push(&current.value);
            Self::in_order_traversal(&current.right, result);
        }
    }

    pub fn pre_order(&self) -> Vec<&T> {
        let mut result = Vec::new();
        Self::pre_order_traversal(&self.root, &mut result);
        result
    }

    fn pre_order_traversal<'a>(node: &'a Option<Box<TreeNode<T>>>, result: &mut Vec<&'a T>) {
        if let Some(current) = node {
            result.push(&current.value);
            Self::pre_order_traversal(&current.left, result);
            Self::pre_order_traversal(&current.right, result);
        }
    }

    pub fn post_order(&self) -> Vec<&T> {
        let mut result = Vec::new();
        Self::post_order_traversal(&self.root, &mut result);
        result
    }

    fn post_order_traversal<'a>(node: &'a Option<Box<TreeNode<T>>>, result: &mut Vec<&'a T>) {
        if let Some(current) = node {
            Self::post_order_traversal(&current.left, result);
            Self::post_order_traversal(&current.right, result);
            result.push(&current.value);
        }
    }

    pub fn level_order(&self) -> Vec<&T> {
        let mut result = Vec::new();
        let mut queue = std::collections::VecDeque::new();
        
        if let Some(root) = &self.root {
            queue.push_back(root.as_ref());
        }

        while let Some(node) = queue.pop_front() {
            result.push(&node.value);
            
            if let Some(left) = &node.left {
                queue.push_back(left.as_ref());
            }
            if let Some(right) = &node.right {
                queue.push_back(right.as_ref());
            }
        }

        result
    }

    // INFORMACIÓN DEL ÁRBOL
    pub fn is_empty(&self) -> bool {
        self.root.is_none()
    }

    pub fn size(&self) -> usize {
        Self::count_nodes(&self.root)
    }

    fn count_nodes(node: &Option<Box<TreeNode<T>>>) -> usize {
        match node {
            Some(current) => {
                1 + Self::count_nodes(&current.left) + Self::count_nodes(&current.right)
            }
            None => 0,
        }
    }

    pub fn height(&self) -> usize {
        Self::calculate_height(&self.root)
    }

    fn calculate_height(node: &Option<Box<TreeNode<T>>>) -> usize {
        match node {
            Some(current) => {
                1 + std::cmp::max(
                    Self::calculate_height(&current.left),
                    Self::calculate_height(&current.right),
                )
            }
            None => 0,
        }
    }

    pub fn min_value(&self) -> Option<&T> {
        Self::find_min_value(&self.root)
    }

    fn find_min_value<'a>(node: &'a Option<Box<TreeNode<T>>>) -> Option<&'a T> {
        match node {
            Some(current) => {
                if current.left.is_some() {
                    Self::find_min_value(&current.left)
                } else {
                    Some(&current.value)
                }
            }
            None => None,
        }
    }

    pub fn max_value(&self) -> Option<&T> {
        Self::find_max_value(&self.root)
    }

    fn find_max_value<'a>(node: &'a Option<Box<TreeNode<T>>>) -> Option<&'a T> {
        match node {
            Some(current) => {
                if current.right.is_some() {
                    Self::find_max_value(&current.right)
                } else {
                    Some(&current.value)
                }
            }
            None => None,
        }
    }

    // VALIDACIÓN Y PROPIEDADES
    pub fn is_bst(&self) -> bool 
    where
        T: Clone + PartialOrd,
    {
        Self::validate_bst(&self.root, None, None)
    }

    fn validate_bst(
        node: &Option<Box<TreeNode<T>>>,
        min: Option<&T>,
        max: Option<&T>,
    ) -> bool {
        match node {
            Some(current) => {
                if let Some(min_val) = min {
                    if &current.value <= min_val {
                        return false;
                    }
                }
                if let Some(max_val) = max {
                    if &current.value >= max_val {
                        return false;
                    }
                }
                Self::validate_bst(&current.left, min, Some(&current.value))
                    && Self::validate_bst(&current.right, Some(&current.value), max)
            }
            None => true,
        }
    }

    // MÉTODOS DE IMPRESIÓN
    pub fn print_in_order(&self) -> String 
    where
        T: Display,
    {
        self.in_order()
            .iter()
            .map(|&value| value.to_string())
            .collect::<Vec<String>>()
            .join("\n") + "\n"
    }

    pub fn print_tree(&self) -> String 
    where
        T: Display,
    {
        let mut result = String::new();
        if let Some(root) = &self.root {
            // Print root
            result.push_str(&format!("{}\n", root.value));
            // Collect children in left, right order if present
            let mut children: Vec<&Box<TreeNode<T>>> = Vec::new();
            if let Some(left) = &root.left {
                children.push(left);
            }
            if let Some(right) = &root.right {
                children.push(right);
            }
            for (i, child) in children.iter().enumerate() {
                let is_tail = i == children.len() - 1;
                Self::print_tree_pretty_node(child, "", is_tail, &mut result);
            }
        }
        result
    }

    fn print_tree_pretty_node(node: &Box<TreeNode<T>>, prefix: &str, is_tail: bool, result: &mut String)
    where
        T: Display,
    {
        result.push_str(&format!("{}{}{}\n", prefix, if is_tail { "└── " } else { "├── " }, node.value));
        // Prepare children (left first, then right)
        let mut children: Vec<&Box<TreeNode<T>>> = Vec::new();
        if let Some(left) = &node.left {
            children.push(left);
        }
        if let Some(right) = &node.right {
            children.push(right);
        }
        for (i, child) in children.iter().enumerate() {
            let tail = i == children.len() - 1;
            let new_prefix = format!("{}{}", prefix, if is_tail { "    " } else { "│   " });
            Self::print_tree_pretty_node(child, &new_prefix, tail, result);
        }
    }
}

// IMPLEMENTACIONES DE TRAIT
impl<T: Ord + Display + Clone> Default for BinaryTree<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T: Ord + Display + Clone> From<Vec<T>> for BinaryTree<T> {
    fn from(values: Vec<T>) -> Self {
        let mut tree = BinaryTree::new();
        for value in values {
            tree.insert(value);
        }
        tree
    }
}

#[cfg(test)]
mod tests {
    use super::BinaryTree;

    #[test]
    fn test_basic_operations() {
        let mut tree = BinaryTree::new();
        tree.insert(5);
        tree.insert(3);
        tree.insert(7);
        tree.insert(1);
        tree.insert(4);

        assert!(tree.contains(5));
        assert!(tree.contains(3));
        assert!(tree.contains(7));
        assert!(!tree.contains(10));

        assert_eq!(tree.size(), 5);
        assert_eq!(tree.height(), 3);
        assert_eq!(tree.min_value(), Some(&1));
        assert_eq!(tree.max_value(), Some(&7));
    }

    #[test]
    fn test_traversals() {
        let mut tree = BinaryTree::new();
        tree.insert(4);
        tree.insert(2);
        tree.insert(6);
        tree.insert(1);
        tree.insert(3);
        tree.insert(5);
        tree.insert(7);

        assert_eq!(
            tree.in_order().iter().map(|&&x| x).collect::<Vec<i32>>(),
            vec![1, 2, 3, 4, 5, 6, 7]
        );
        
        assert_eq!(
            tree.pre_order().iter().map(|&&x| x).collect::<Vec<i32>>(),
            vec![4, 2, 1, 3, 6, 5, 7]
        );
        
        assert_eq!(
            tree.level_order().iter().map(|&&x| x).collect::<Vec<i32>>(),
            vec![4, 2, 6, 1, 3, 5, 7]
        );
    }

    #[test]
    fn test_removal() {
        let mut tree = BinaryTree::new();
        tree.insert(5);
        tree.insert(3);
        tree.insert(7);
        tree.insert(2);
        tree.insert(4);

        assert!(tree.remove(3));
        assert!(!tree.contains(3));
        assert_eq!(tree.size(), 4);
        assert!(tree.is_bst());
    }

    #[test]
    fn test_empty_tree() {
        let tree: BinaryTree<i32> = BinaryTree::new();
        assert!(tree.is_empty());
        assert_eq!(tree.size(), 0);
        assert_eq!(tree.height(), 0);
        assert_eq!(tree.min_value(), None);
        assert_eq!(tree.max_value(), None);
    }

    #[test]
    fn test_printing() {
        let mut tree = BinaryTree::new();
        tree.insert(3);
        tree.insert(1);
        tree.insert(4);
        tree.insert(2);

        let in_order_str = tree.print_in_order();
        println!("{}", in_order_str);
        assert_eq!(in_order_str, "1\n2\n3\n4\n");

        let tree_str = tree.print_tree();
        println!("{}", tree_str);
        let expected_str = "3\n├── 1\n│   └── 2\n└── 4\n";
        assert_eq!(tree_str, expected_str);
    }

    #[test]
    fn test_contains_and_find() {
        let mut tree = BinaryTree::new();
        tree.insert(10);
        tree.insert(5);
        tree.insert(15);

        assert!(tree.contains(10));
        assert!(tree.contains(5));
        assert!(!tree.contains(20));

        let node = tree.find(&5);
        assert!(node.is_some());
        assert_eq!(node.unwrap().value, 5);

        let missing_node = tree.find(&20);
        assert!(missing_node.is_none());
    }

    #[test]
    fn test_from_vec() {
        let values = vec![5, 3, 7, 1, 4];
        let tree = BinaryTree::from(values);
        
        assert!(tree.contains(5));
        assert!(tree.contains(3));
        assert!(tree.contains(7));
        assert!(tree.contains(1));
        assert!(tree.contains(4));
        assert!(!tree.contains(10));
        
        assert_eq!(tree.size(), 5);
        assert_eq!(tree.height(), 3);
    }
}