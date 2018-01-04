Snapshot Handler
---------------

This chunk of python script will aim to help organise snapshots of LV's for archival purposes. It is written with the goal of having both a regular backup, but also to provide a static number of snapshots to be able to limit the amount of potential storage used by each one.
It does this by taking a list of days in the past from config.cfg, and trying to find the closest existing snapshot to that point. It does this independent of whatever snapshots already exist, by referencing the creation times in LVM. If there are more snapshots needed than the times set, it will then remove the excess. Lastly, it will attempt to create a new snapshot for today, according to a standard format.
