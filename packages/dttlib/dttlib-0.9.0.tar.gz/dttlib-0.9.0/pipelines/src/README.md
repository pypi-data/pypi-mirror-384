# Design

Keep existing pipeline traits

Except pass state and config structs

Maybe drop passing segments.

Implement the traits with Pipeline type maybe
stateless becomes Pipeline with config

pure becomes stateless without config - just a wrapper around stateless start

Make the stateless pipeline a struct that implements pipeline rather than its own
set of traits


Function wrappers that 

- take a stateless function and make it a stateful function 
with an empty state.
- take a stateful function with no config and add empty config
- Take a pure function and make it a stateless function with empty config
- Take a function that returns a single value and turn into a function that returns a vector of size 1
- Take a function that returns a vector and turn it into a generator function
- Take a synchronous function and turn it into an async function with spawn blocking
