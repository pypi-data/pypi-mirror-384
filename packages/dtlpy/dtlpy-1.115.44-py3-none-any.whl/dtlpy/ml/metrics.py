import numpy as np
import pandas as pd
import logging
import datetime

from .. import entities

logger = logging.getLogger(name='dtlpy')


class Results:
    def __init__(self, matches, annotation_type):
        self.matches = matches
        self.annotation_type = annotation_type

    def to_df(self):
        return self.matches.to_df()

    def summary(self):
        df = self.matches.to_df()
        total_set_one = len(df['first_id'].dropna())
        total_set_two = len(df['second_id'].dropna())
        # each set unmatched is the number of Nones from the other set
        unmatched_set_one = df.shape[0] - total_set_two
        unmatched_set_two = df.shape[0] - total_set_one
        matched_set_one = total_set_one - unmatched_set_one
        matched_set_two = total_set_two - unmatched_set_two
        # sanity
        assert matched_set_one == matched_set_two, 'matched numbers are not the same'
        assert df['annotation_score'].shape[0] == (unmatched_set_one + unmatched_set_two + matched_set_one), \
            'mis-match number if scores and annotations'
        return {
            'annotation_type': self.annotation_type,
            'mean_annotations_scores': df['annotation_score'].mean(),
            'mean_attributes_scores': df['attribute_score'].mean(),
            'mean_labels_scores': df['label_score'].mean(),
            'n_annotations_set_one': total_set_one,
            'n_annotations_set_two': total_set_two,
            'n_annotations_total': total_set_one + total_set_two,
            'n_annotations_unmatched_set_one': unmatched_set_one,
            'n_annotations_unmatched_set_two': unmatched_set_two,
            'n_annotations_unmatched_total': unmatched_set_one + unmatched_set_two,
            'n_annotations_matched_total': matched_set_one,
            'precision': matched_set_one / (matched_set_one + unmatched_set_two),
            'recall': matched_set_one / (matched_set_one + unmatched_set_one)
        }


class Match:
    def __init__(self,
                 first_annotation_id, first_annotation_label, first_annotation_confidence,
                 second_annotation_id, second_annotation_label, second_annotation_confidence,
                 # defaults
                 annotation_score=0, attributes_score=0, geometry_score=0, label_score=0):
        """
        Save a match between two annotations with all relevant scores

        :param first_annotation_id:
        :param second_annotation_id:
        :param annotation_score:
        :param attributes_score:
        :param geometry_score:
        :param label_score:
        """
        self.first_annotation_id = first_annotation_id
        self.first_annotation_label = first_annotation_label
        self.first_annotation_confidence = first_annotation_confidence
        self.second_annotation_id = second_annotation_id
        self.second_annotation_label = second_annotation_label
        self.second_annotation_confidence = second_annotation_confidence
        self.annotation_score = annotation_score
        self.attributes_score = attributes_score
        # Replace the old annotation score
        self.geometry_score = geometry_score
        self.label_score = label_score

    def __repr__(self):
        return 'annotation: {:.2f}, attributes: {:.2f}, geometry: {:.2f}, label: {:.2f}'.format(
            self.annotation_score, self.attributes_score, self.geometry_score, self.label_score)


class Matches:
    def __init__(self):
        self.matches = list()
        self._annotations_raw_df = list()

    def __len__(self):
        return len(self.matches)

    def __repr__(self):
        return self.to_df().to_string()

    def to_df(self):
        results = list()
        for match in self.matches:
            results.append({
                'first_id': match.first_annotation_id,
                'first_label': match.first_annotation_label,
                'first_confidence': match.first_annotation_confidence,
                'second_id': match.second_annotation_id,
                'second_label': match.second_annotation_label,
                'second_confidence': match.second_annotation_confidence,
                'annotation_score': match.annotation_score,
                'attribute_score': match.attributes_score,
                'geometry_score': match.geometry_score,
                'label_score': match.label_score,
            })
        df = pd.DataFrame(results)
        return df

    def add(self, match: Match):
        self.matches.append(match)

    def validate(self):
        first = list()
        second = list()
        for match in self.matches:
            if match.first_annotation_id in first:
                raise ValueError('duplication for annotation id {!r} in FIRST set'.format(match.first_annotation_id))
            if match.first_annotation_id is not None:
                first.append(match.first_annotation_id)
            if match.second_annotation_id in second:
                raise ValueError('duplication for annotation id {!r} in SECOND set'.format(match.second_annotation_id))
            if match.second_annotation_id is not None:
                second.append(match.second_annotation_id)
        return True

    def find(self, annotation_id, loc='first'):
        for match in self.matches:
            if loc == 'first':
                if match.first_annotation_id == annotation_id:
                    return match
            elif loc == 'second':
                if match.second_annotation_id == annotation_id:
                    return match
        raise ValueError('could not find annotation id {!r} in {}'.format(annotation_id, loc))


######################
# Matching functions #
######################
class Matchers:

    @staticmethod
    def calculate_iou_box(pts1, pts2, config):
        """
        Measure the two list of points IoU
        :param pts1: ann.geo coordinates
        :param pts2: ann.geo coordinates
        :return: `float` how Intersection over Union of tho shapes
        """
        try:
            from shapely.geometry import Polygon
        except (ImportError, ModuleNotFoundError) as err:
            raise RuntimeError('dtlpy depends on external package. Please install ') from err
        if len(pts1) == 2:
            # regular box annotation (2 pts)
            pt1_left_top = [pts1[0][0], pts1[0][1]]
            pt1_right_top = [pts1[0][0], pts1[1][1]]
            pt1_right_bottom = [pts1[1][0], pts1[1][1]]
            pt1_left_bottom = [pts1[1][0], pts1[0][1]]
        else:
            # rotated box annotation (4 pts)
            pt1_left_top = pts1[0]
            pt1_right_top = pts1[3]
            pt1_left_bottom = pts1[1]
            pt1_right_bottom = pts1[2]

        poly_1 = Polygon([pt1_left_top,
                          pt1_right_top,
                          pt1_right_bottom,
                          pt1_left_bottom])

        if len(pts2) == 2:
            # regular box annotation (2 pts)
            pt2_left_top = [pts2[0][0], pts2[0][1]]
            pt2_right_top = [pts2[0][0], pts2[1][1]]
            pt2_right_bottom = [pts2[1][0], pts2[1][1]]
            pt2_left_bottom = [pts2[1][0], pts2[0][1]]
        else:
            # rotated box annotation (4 pts)
            pt2_left_top = pts2[0]
            pt2_right_top = pts2[3]
            pt2_left_bottom = pts2[1]
            pt2_right_bottom = pts2[2]

        poly_2 = Polygon([pt2_left_top,
                          pt2_right_top,
                          pt2_right_bottom,
                          pt2_left_bottom])
        iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area
        return iou

    @staticmethod
    def calculate_iou_classification(pts1, pts2, config):
        """
        Measure the two list of points IoU
        :param pts1: ann.geo coordinates
        :param pts2: ann.geo coordinates
        :return: `float` how Intersection over Union of tho shapes
        """
        return 1

    @staticmethod
    def calculate_iou_polygon(pts1, pts2, config):
        try:
            # from shapely.geometry import Polygon
            import cv2
        except (ImportError, ModuleNotFoundError) as err:
            raise RuntimeError('dtlpy depends on external package. Please install ') from err
        # # using shapley
        # poly_1 = Polygon(pts1)
        # poly_2 = Polygon(pts2)
        # iou = poly_1.intersection(poly_2).area / poly_1.union(poly_2).area

        # # using opencv
        width = int(np.ceil(np.max(np.concatenate((pts1[:, 0], pts2[:, 0]))))) + 10
        height = int(np.ceil(np.max(np.concatenate((pts1[:, 1], pts2[:, 1]))))) + 10
        mask1 = np.zeros((height, width))
        mask2 = np.zeros((height, width))
        mask1 = cv2.drawContours(
            image=mask1,
            contours=[pts1.round().astype(int)],
            contourIdx=-1,
            color=1,
            thickness=-1,
        )
        mask2 = cv2.drawContours(
            image=mask2,
            contours=[pts2.round().astype(int)],
            contourIdx=-1,
            color=1,
            thickness=-1,
        )
        iou = np.sum((mask1 + mask2) == 2) / np.sum((mask1 + mask2) > 0)
        if np.sum((mask1 + mask2) > 2):
            assert False
        return iou

    @staticmethod
    def calculate_iou_semantic(mask1, mask2, config):
        joint_mask = mask1 + mask2
        return np.sum(np.sum(joint_mask == 2) / np.sum(joint_mask > 0))

    @staticmethod
    def calculate_iou_point(pt1, pt2, config):
        """
        pt is [x,y]
        normalizing  to score  between [0, 1] -> 1 is the exact match
        if same point score is 1
        at about 20 pix distance score is about 0.5, 100 goes to 0
        :param pt1:
        :param pt2:
        :return:
        """
        """
        x = np.arange(int(diag))
        y = np.exp(-1 / diag * 20 * x)
        plt.figure()
        plt.plot(x, y)
        """
        height = config.get('height', 500)
        width = config.get('width', 500)
        diag = np.sqrt(height ** 2 + width ** 2)
        # 20% of the image diagonal tolerance (empirically). need to
        return np.exp(-1 / diag * 20 * np.linalg.norm(np.asarray(pt1) - np.asarray(pt2)))

    @staticmethod
    def match_attributes(attributes1, attributes2):
        """
        Returns IoU of the attributes. if both are empty - its a prefect match (returns 1)
        0: no matching
        1: perfect attributes match
        """
        if type(attributes1) is not type(attributes2):
            logger.warning('attributes are not same type: {}, {}'.format(type(attributes1), type(attributes2)))
            return 0

        if attributes1 is None and attributes2 is None:
            return 1

        if isinstance(attributes1, dict) and isinstance(attributes2, dict):
            # convert to list
            attributes1 = ['{}-{}'.format(key, val) for key, val in attributes1.items()]
            attributes2 = ['{}-{}'.format(key, val) for key, val in attributes2.items()]

        intersection = set(attributes1).intersection(set(attributes2))
        union = set(attributes1).union(attributes2)
        if len(union) == 0:
            # if there is no union - there are no attributes at all
            return 1
        return len(intersection) / len(union)

    @staticmethod
    def match_labels(label1, label2):
        """
        Returns 1 in one of the labels in substring of the second
        """
        return int(label1 in label2 or label2 in label1)

    @staticmethod
    def general_match(matches: Matches,
                      first_set: entities.AnnotationCollection,
                      second_set: entities.AnnotationCollection,
                      match_type,
                      match_threshold: float,
                      ignore_attributes=False,
                      ignore_labels=False):
        """

        :param matches:
        :param first_set:
        :param second_set:
        :param match_type:
        :param match_threshold:
        :param ignore_attributes:
        :param ignore_labels:
        :return:
        """
        annotation_type_to_func = {
            entities.AnnotationType.BOX: Matchers.calculate_iou_box,
            entities.AnnotationType.CLASSIFICATION: Matchers.calculate_iou_classification,
            entities.AnnotationType.SEGMENTATION: Matchers.calculate_iou_semantic,
            entities.AnnotationType.POLYGON: Matchers.calculate_iou_polygon,
            entities.AnnotationType.POINT: Matchers.calculate_iou_point,
        }
        df = pd.DataFrame(data=-1 * np.ones((len(second_set), len(first_set))),
                          columns=[a.id for a in first_set],
                          index=[a.id for a in second_set])
        for annotation_one in first_set:
            for annotation_two in second_set:
                if match_type not in annotation_type_to_func:
                    raise ValueError('unsupported type: {}'.format(match_type))
                if df[annotation_one.id][annotation_two.id] == -1:
                    try:
                        config = {'height': annotation_one._item.height if annotation_one._item is not None else 500,
                                  'width': annotation_one._item.width if annotation_one._item is not None else 500}
                        df[annotation_one.id][annotation_two.id] = annotation_type_to_func[match_type](
                            annotation_one.geo,
                            annotation_two.geo,
                            config)
                    except ZeroDivisionError:
                        logger.warning(
                            'Found annotations with area=0!: annotations ids: {!r}, {!r}'.format(annotation_one.id,
                                                                                                 annotation_two.id))
                        df[annotation_one.id][annotation_two.id] = 0
        # for debug - save the annotations scoring matrix
        matches._annotations_raw_df.append(df.copy())

        # go over all matches
        while True:
            # take max IoU score, list the match and remove annotations' ids from columns and rows
            # keep doing that until no more matches or lower than match threshold
            max_cell = df.max().max()
            if max_cell < match_threshold or np.isnan(max_cell):
                break
            row_index, col_index = np.where(df == max_cell)
            row_index = row_index[0]
            col_index = col_index[0]
            first_annotation_id = df.columns[col_index]
            second_annotation_id = df.index[row_index]
            first_annotation = [a for a in first_set if a.id == first_annotation_id][0]
            second_annotation = [a for a in second_set if a.id == second_annotation_id][0]
            geometry_score = df.iloc[row_index, col_index]
            labels_score = Matchers.match_labels(label1=first_annotation.label,
                                                 label2=second_annotation.label)
            attribute_score = Matchers.match_attributes(attributes1=first_annotation.attributes,
                                                        attributes2=second_annotation.attributes)

            # TODO use ignores for final score
            annotation_score = (geometry_score + attribute_score + labels_score) / 3
            matches.add(Match(first_annotation_id=first_annotation_id,
                              first_annotation_label=first_annotation.label,
                              first_annotation_confidence=
                              first_annotation.metadata.get('user', dict()).get('model', dict()).get('confidence', 1),
                              second_annotation_id=second_annotation_id,
                              second_annotation_label=second_annotation.label,
                              second_annotation_confidence=
                              second_annotation.metadata.get('user', dict()).get('model', dict()).get('confidence', 1),
                              geometry_score=geometry_score,
                              annotation_score=annotation_score,
                              label_score=labels_score,
                              attributes_score=attribute_score))
            df.drop(index=second_annotation_id, inplace=True)
            df.drop(columns=first_annotation_id, inplace=True)
        # add un-matched
        for second_id in df.index:
            second_annotation = [a for a in second_set if a.id == second_id][0]
            matches.add(match=Match(first_annotation_id=None,
                                    first_annotation_label=None,
                                    first_annotation_confidence=None,
                                    second_annotation_id=second_id,
                                    second_annotation_label=second_annotation.label,
                                    second_annotation_confidence=
                                    second_annotation.metadata.get('user', dict()).get('model', dict()).get(
                                        'confidence', 1),
                                    ))
        for first_id in df.columns:
            first_annotation = [a for a in first_set if a.id == first_id][0]
            matches.add(match=Match(first_annotation_id=first_id,
                                    first_annotation_label=first_annotation.label,
                                    first_annotation_confidence=
                                    first_annotation.metadata.get('user', dict()).get('model', dict()).get('confidence',
                                                                                                           1),
                                    second_annotation_id=None,
                                    second_annotation_label=None,
                                    second_annotation_confidence=None))
        return matches


def item_annotation_duration(item: entities.Item = None,
                             dataset: entities.Dataset = None,
                             project: entities.Project = None,
                             task: entities.Task = None,
                             assignment: entities.Assignment = None):
    if all(ent is None for ent in [item, dataset, project, assignment, task]):
        raise ValueError('At least one input to annotation duration must not be None')
    query = {
        "startTime": 0,
        "context": {
            "accountId": [],
            "orgId": [],
            "projectId": [],
            "datasetId": [],
            "taskId": [],
            "assignmentId": [],
            "itemId": [],
            "userId": [],
            "serviceId": [],
            "podId": [],
        },
        "measures": [
            {
                "measureType": "itemAnnotationDuration",
                "pageSize": 1000,
                "page": 0,
            },
        ]
    }
    # add context for analytics
    created_at = list()
    if item is not None:
        query['context']['itemId'].append(item.id)
        created_at.append(int(1000 * datetime.datetime.fromisoformat(item.created_at[:-1]).timestamp()))
    if task is not None:
        query['context']['taskId'].append(task.id)
        created_at.append(int(1000 * datetime.datetime.fromisoformat(task.created_at[:-1]).timestamp()))
    if dataset is not None:
        query['context']['datasetId'].append(dataset.id)
        created_at.append(int(1000 * datetime.datetime.fromisoformat(dataset.created_at[:-1]).timestamp()))
    if assignment is not None:
        query['context']['assignmentId'].append(assignment.id)
        # assignment doesnt have "created_at" attribute
    query['startTime'] = int(np.min(created_at))
    raw = project.analytics.get_samples(query=query, return_field=None, return_raw=True)
    res = {row['itemId']: row['duration'] for row in raw[0]['response']}
    if item.id not in res:
        total_time_s = 0
    else:
        total_time_s = res[item.id] / 1000
    return total_time_s
