# Usage

## Activity Exchange

In vanilla cattle_grid, there are two routing_keys on
the Activity Exchange, you should send messages to:

- `send_message` ... performs POST inbox in the Fediverse
- `fetch_object` ... returns GET object in the Fediverse

## Rewriting actions

The [Simple Storage Extension](../extensions/simple_storage.md)
defines the `publish_activity` and `publish_object` methods
to handle storage and subsequent publishing of an activity
respectively an object.

People can then develop clients that use these two methods
to publish activities and objects, thus providing a more or
less full Fediverse experience on the client side. If you now
want to change the behavior of `publish_activity` and `publish_object`,
you could replace the simple storage extension. This is doable,
but a big change. In order to do smaller grained changes, one
can use the mechanism of rewriting method names provided
by [rewrite_method][cattle_grid.config.rewrite.RewriteConfiguration].
