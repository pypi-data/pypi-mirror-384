/// A wrapper that adheres to the standard formatting rules
/// 
/// ```rust
/// let z = 1024_i64;
/// let f = Prettier(z);
/// 
/// assert_eq!("001_024", format!("{f:06}"));
/// ```
