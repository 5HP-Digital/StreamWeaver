using Microsoft.EntityFrameworkCore.ChangeTracking;

namespace IPTV.JobWorker.Data.Comparers;

public class StringArrayComparer() : ValueComparer<string[]>(
    (c1, c2) => (c1 == null && c2 == null) || (c1 != null && c2 != null && c1.SequenceEqual(c2)),
    c => c.Aggregate(1, (a, v) => HashCode.Combine(a, v.GetHashCode())),
    c => c);