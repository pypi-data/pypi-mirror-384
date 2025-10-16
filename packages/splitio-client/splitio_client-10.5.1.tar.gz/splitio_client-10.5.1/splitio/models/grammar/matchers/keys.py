"""Keys matchers module."""
from splitio.models.grammar.matchers.base import Matcher


class AllKeysMatcher(Matcher):
    """A matcher that always returns True."""

    def _build(self, raw_matcher):
        """
        Build an AllKeysMatcher.

        :param raw_matcher: raw matcher as fetched from splitChanges response.
        :type raw_matcher: dict
        """
        pass

    def _match(self, key, attributes=None, context=None):
        """
        Evaluate user input against a matcher and return whether the match is successful.

        :param key: User key.
        :type key: str.
        :param attributes: Custom user attributes.
        :type attributes: dict.
        :param context: Evaluation context
        :type context: dict

        :returns: Wheter the match is successful.
        :rtype: bool
        """
        return key is not None

    def __str__(self):
        """Return string Representation."""
        return 'in segment all'

    def _add_matcher_specific_properties_to_json(self):
        """Add matcher specific properties to base dict before returning it."""
        return {}


class UserDefinedSegmentMatcher(Matcher):
    """Matcher that returns true when the submitted key belongs to a segment."""

    def _build(self, raw_matcher):
        """
        Build an UserDefinedSegmentMatcher.

        :param raw_matcher: raw matcher as fetched from splitChanges response.
        :type raw_matcher: dict
        """
        self._segment_name = raw_matcher['userDefinedSegmentMatcherData']['segmentName']

    def _match(self, key, attributes=None, context=None):
        """
        Evaluate user input against a matcher and return whether the match is successful.

        :param key: User key.
        :type key: str.
        :param attributes: Custom user attributes.
        :type attributes: dict.
        :param context: Evaluation context
        :type context: dict

        :returns: Wheter the match is successful.
        :rtype: bool
        """
        matching_data = self._get_matcher_input(key, attributes)
        if matching_data is None:
            return False

        return context['ec'].segment_memberships[self._segment_name]

    def _add_matcher_specific_properties_to_json(self):
        """Return UserDefinedSegment specific properties."""
        return {
            'userDefinedSegmentMatcherData': {
                'segmentName': self._segment_name
            }
        }

    def __str__(self):
        """Return string Representation."""
        return 'in segment {segment_name}'.format(
            segment_name=self._segment_name
        )
