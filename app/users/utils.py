from app.models import Claim, Level
from app import db
import logging


def assign_rank_to_claim(claim, new_rank, admin_id=None):
    """
    Assign a specific rank (1-50 or None) to a claim within its level.

    Args:
        claim: Claim object to rank
        new_rank: Integer 1-50 or None (for unranked)
        admin_id: Admin user ID performing the assignment (optional)

    Returns:
        tuple: (success: bool, message: str)
    """
    if claim.status != 'approved':
        return (False, 'Can only assign ranks to approved claims')

    # Validate rank
    if new_rank is not None:
        if not isinstance(new_rank, int) or new_rank < 1 or new_rank > 50:
            return (False, 'Rank must be between 1 and 50, or None for unranked')

    try:
        # If setting to unranked
        if new_rank is None:
            old_rank = claim.rank
            claim.rank = None
            claim.points = 0

            # If claim had a rank, close the gap by shifting claims up
            if old_rank and 1 <= old_rank <= 50:
                claims_to_shift_up = Claim.query.filter(
                    Claim.level_id == claim.level_id,
                    Claim.rank > old_rank,
                    Claim.rank <= 50,
                    Claim.status == 'approved',
                    Claim.id != claim.id
                ).order_by(Claim.rank.asc()).all()

                for c in claims_to_shift_up:
                    c.rank = c.rank - 1
                    c.points = 51 - c.rank

            db.session.commit()
            return (True, f'Claim #{claim.id} set to unranked')

        # Remember old rank to handle gaps
        old_rank = claim.rank

        # Handle rank adjustment based on movement direction
        if old_rank and 1 <= old_rank <= 50 and old_rank != new_rank:
            # Claim is moving from one rank to another
            if old_rank < new_rank:
                # Moving down (e.g., rank 3 to rank 7)
                # Claims between old_rank and new_rank shift up
                claims_to_shift_up = Claim.query.filter(
                    Claim.level_id == claim.level_id,
                    Claim.rank > old_rank,
                    Claim.rank <= new_rank,
                    Claim.status == 'approved',
                    Claim.id != claim.id
                ).order_by(Claim.rank.asc()).all()

                for c in claims_to_shift_up:
                    c.rank = c.rank - 1
                    c.points = 51 - c.rank

            else:  # old_rank > new_rank
                # Moving up (e.g., rank 7 to rank 3)
                # Claims between new_rank and old_rank shift down
                claims_to_shift_down = Claim.query.filter(
                    Claim.level_id == claim.level_id,
                    Claim.rank >= new_rank,
                    Claim.rank < old_rank,
                    Claim.status == 'approved',
                    Claim.id != claim.id
                ).order_by(Claim.rank.desc()).all()

                for c in claims_to_shift_down:
                    c.rank = c.rank + 1
                    if c.rank > 50:
                        c.rank = None
                        c.points = 0
                    else:
                        c.points = 51 - c.rank

        elif not old_rank or old_rank > 50:
            # Claim is being ranked for the first time or was unranked
            # Shift all claims at new_rank and below down by 1
            claims_to_shift_down = Claim.query.filter(
                Claim.level_id == claim.level_id,
                Claim.rank >= new_rank,
                Claim.rank <= 50,
                Claim.status == 'approved',
                Claim.id != claim.id
            ).order_by(Claim.rank.desc()).all()

            for c in claims_to_shift_down:
                c.rank = c.rank + 1
                if c.rank > 50:
                    c.rank = None
                    c.points = 0
                else:
                    c.points = 51 - c.rank

        # Assign the new rank
        claim.rank = new_rank
        claim.points = 51 - new_rank

        db.session.commit()

        level_name = claim.level.name if claim.level else f'Level #{claim.level_id}'
        return (True, f'Claim #{claim.id} assigned rank #{new_rank} in {level_name}')

    except Exception as e:
        db.session.rollback()
        logging.error(f'Error assigning rank: {str(e)}')
        return (False, f'Error assigning rank: {str(e)}')


def get_level_rank_distribution(level_id):
    """
    Get current rank distribution for a level.

    Args:
        level_id: ID of the level

    Returns:
        dict: {
            'ranked_count': Number of claims with ranks 1-50,
            'unranked_count': Number of approved claims without rank,
            'next_available_rank': Lowest unused rank 1-50 or None if full,
            'rank_gaps': List of unused ranks within 1-50
        }
    """
    # Count ranked claims
    ranked_claims = Claim.query.filter_by(
        level_id=level_id,
        status='approved'
    ).filter(Claim.rank.isnot(None)).all()

    # Count unranked approved claims
    unranked_count = Claim.query.filter_by(
        level_id=level_id,
        status='approved'
    ).filter(Claim.rank.is_(None)).count()

    # Find occupied ranks
    occupied_ranks = {claim.rank for claim in ranked_claims if claim.rank and 1 <= claim.rank <= 50}

    # Find gaps in 1-50
    all_ranks = set(range(1, 51))
    rank_gaps = sorted(all_ranks - occupied_ranks)

    # Next available rank
    next_available = rank_gaps[0] if rank_gaps else None

    return {
        'ranked_count': len(occupied_ranks),
        'unranked_count': unranked_count,
        'next_available_rank': next_available,
        'rank_gaps': rank_gaps
    }


def recalculate_points_for_level(level_id):
    """
    Recalculate points for all claims in a level based on current ranks.
    Points are calculated as 51 - rank for ranks 1-50, 0 for unranked.

    Args:
        level_id: ID of the level

    Returns:
        int: Number of claims updated
    """
    claims = Claim.query.filter_by(
        level_id=level_id,
        status='approved'
    ).all()

    updated_count = 0
    for claim in claims:
        if claim.rank and 1 <= claim.rank <= 50:
            claim.points = 51 - claim.rank
            updated_count += 1
        else:
            claim.points = 0
            updated_count += 1

    db.session.commit()
    return updated_count


def recalculate_ranks():
    """
    DEPRECATED: This function calculated global ranks based on votes.
    Now ranks are assigned manually per-level by admins.

    Kept for backward compatibility during transition.
    Use assign_rank_to_claim() instead.
    """
    logging.warning("recalculate_ranks() is deprecated. Use per-level manual assignment instead.")

    # Original implementation kept for backward compatibility
    approved_claims = Claim.query.filter_by(status='approved')\
        .order_by(Claim.vote_count.desc(), Claim.submitted_at.asc())\
        .all()

    for index, claim in enumerate(approved_claims):
        claim.rank = index + 1

        if claim.rank <= 50:
            claim.points = 51 - claim.rank
        else:
            claim.points = 0

    db.session.commit()
    return len(approved_claims)
